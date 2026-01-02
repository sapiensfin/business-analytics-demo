import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Налаштування сторінки
st.set_page_config(page_title="SapiensFin | Demo", layout="wide")

# Очищення кешу при зміні структури (допомагає уникнути KeyError)
st.cache_data.clear()

# 2. ГЕНЕРАЦІЯ ДАНИХ
@st.cache_data
def get_data():
    data = []
    months = pd.date_range(start="2025-01-01", periods=12, freq='MS')
    
    categories = {
        'Оренда та склад': 55000,
        'Зарплата офіс': 65000,
        'Зарплата водії': 180000,
        'ПММ (Паливо)': 95000,
        'Лізинг авто': 75000,
        'Ремонт та сервіс': 25000,
        'Маркетинг': 20000,
        'Податки та збори': 55000,
        'Амортизація': 10000
    }

    for month in months:
        m_num = month.month
        # Сезонні коефіцієнти
        rev_f = 0.6 if m_num in [3, 10] else 1.0
        rep_f = 3.5 if m_num in [3, 10] else 1.0
        
        # Доходи
        data.append({'Дата': month, 'Тип': '1. ДОХОДИ', 'Стаття': 'Виручка (B2B)', 'Значення': float(600000 * rev_f)})
        
        # Витрати
        for cat, amt in categories.items():
            val = amt * rep_f if cat == 'Ремонт та сервіс' else amt
            data.append({'Дата': month, 'Тип': '2. ВИТРАТИ', 'Стаття': cat, 'Значення': float(val)})
            
    return pd.DataFrame(data)

# 3. БІЧНА ПАНЕЛЬ
with st.sidebar:
    st.markdown("### 🚀 Sapiens Fin")
    st.write("---")
    st.header("🕹️ Симулятор")
    price_inc = st.slider("Збільшення цін (%)", 0, 50, 0)
    cost_red = st.slider("Оптимізація витрат (%)", 0, 50, 0)
    init_bal = st.number_input("Стартовий капітал (PLN)", value=100000)

# 4. ОБРОБКА
df = get_data().copy()

# Симуляція (використовуємо 'Значення')
df.loc[df['Тип'] == '1. ДОХОДИ', 'Значення'] *= (1 + price_inc / 100)
df.loc[df['Тип'] == '2. ВИТРАТИ', 'Значення'] *= (1 - cost_red / 100)

df['Місяць'] = df['Дата'].dt.strftime('%m-%Y')

# Метрики
total_rev = df[df['Тип'] == '1. ДОХОДИ']['Значення'].sum()
total_exp = df[df['Тип'] == '2. ВИТРАТИ']['Значення'].sum()
profit = total_rev - total_exp
ros = (profit / total_rev * 100) if total_rev > 0 else 0

# 5. ВІДОБРАЖЕННЯ
st.title("Financial Strategy Dashboard")

col1, col2, col3 = st.columns(3)
col1.metric("Річний оборот", f"{total_rev:,.0f} PLN")
col2.metric("Чистий прибуток", f"{profit:,.0f} PLN")
col3.metric("Рентабельність (ROS)", f"{ros:.1f}%")

# 6. WATERFALL CHART
st.divider()
st.subheader("💎 Waterfall: Від виручки до прибутку")
exp_agg = df[df['Тип'] == '2. ВИТРАТИ'].groupby('Стаття')['Значення'].sum().sort_values(ascending=False)

fig_wf = go.Figure(go.Waterfall(
    measure = ["relative"] * (len(exp_agg) + 1) + ["total"],
    x = ["Виручка"] + list(exp_agg.index) + ["Чистий прибуток"],
    y = [total_rev] + [-v for v in exp_agg.values] + [0],
    connector = {"line":{"color":"rgba(63, 63, 63, 0.5)"}},
))
st.plotly_chart(fig_wf, use_container_width=True)

# 7. КРУГОВІ ДІАГРАМИ
st.divider()
st.subheader("📊 Структура витрат: Порівняння")
p_col1, p_col2 = st.columns(2)

for i, col in enumerate([p_col1, p_col2]):
    m_target = 1 if i == 0 else 12
    p_data = df[(df['Тип'] == '2. ВИТРАТИ') & (df['Дата'].dt.month == m_target)]
    fig = go.Figure(data=[go.Pie(labels=p_data['Стаття'], values=p_data['Значення'], hole=.4)])
    fig.update_layout(title="Січень" if i == 0 else "Грудень", height=380)
    col.plotly_chart(fig, use_container_width=True)

# 8. P&L ТАБЛИЦЯ (ВИПРАВЛЕНО KeyError)
st.divider()
st.subheader("📑 Звіт P&L за місяцями")

# Використовуємо 'Значення', що відповідає DF
pnl = df.pivot_table(
    index=['Тип', 'Стаття'], 
    columns='Місяць', 
    values='Значення', 
    aggfunc='sum'
)

# Сортування колонок
sorted_months = sorted(df['Місяць'].unique(), key=lambda x: pd.to_datetime(x, format='%m-%Y'))
pnl = pnl[sorted_months]

st.dataframe(
    pnl.style.format("{:,.0f}")
    .background_gradient(cmap='Greens', subset=pd.IndexSlice[('1. ДОХОДИ', slice(None)), :])
    .background_gradient(cmap='Reds', subset=pd.IndexSlice[('2. ВИТРАТИ', slice(None)), :]),
    use_container_width=True
)

# 9. CASH FLOW
st.divider()
st.subheader("📉 Прогноз Cash Flow")
df['Change'] = df.apply(lambda x: x['Значення'] if 'ДОХОДИ' in x['Тип'] else -x['Значення'], axis=1)
cf_daily = df.groupby('Дата')['Change'].sum().reset_index()
cf_daily['Balance'] = init_bal + cf_daily['Change'].cumsum()

fig_cf = go.Figure()
fig_cf.add_trace(go.Scatter(x=cf_daily['Дата'], y=cf_daily['Balance'], fill='tozeroy', line_color='#00CC96'))
st.plotly_chart(fig_cf, use_container_width=True)

if cf_daily['Balance'].min() < 0:
    st.error(f"🚨 Касовий розрив: {cf_daily['Balance'].min():,.0f} PLN")
else:
    st.success("✅ Фінансова модель стійка.")
