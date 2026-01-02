import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Налаштування сторінки
st.set_page_config(page_title="SapiensFin | Professional Demo", layout="wide")

# 2. ГЕНЕРАЦІЯ ДАНИХ
@st.cache_data
def get_base_data():
    data = []
    months = pd.date_range(start="2025-01-01", periods=12, freq='MS')
    
    # Категорії українською
    expense_categories = {
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
        rev_f = 0.6 if m_num in [3, 10] else 1.0
        rep_f = 3.5 if m_num in [3, 10] else 1.0
        
        # Дохід (Income)
        data.append({'Дата': month, 'Тип': '1. ДОХОДИ', 'Стаття': 'Виручка (B2B)', 'Сума': float(600000 * rev_f)})
        
        # Витрати (Expenses)
        for cat, amt in expense_categories.items():
            val = amt * rep_f if cat == 'Ремонт та сервіс' else amt
            data.append({'Дата': month, 'Тип': '2. ВИТРАТИ', 'Стаття': cat, 'Сума': float(val)})
            
    return pd.DataFrame(data)

# 3. БІЧНА ПАНЕЛЬ
with st.sidebar:
    st.header("🕹️ Симулятор")
    price_inc = st.slider("Збільшення цін (%)", 0, 50, 0)
    cost_red = st.slider("Оптимізація витрат (%)", 0, 50, 0)
    init_bal = st.number_input("Стартовий капітал (PLN)", value=100000)
    st.write("---")
    st.markdown("[sapiensfin.eu](https://sapiensfin.eu)")

# 4. ОБРОБКА ДАНИХ
df_base = get_base_data()
df = df_base.copy()

# Застосовуємо симуляцію
df.loc[df['Тип'] == '1. ДОХОДИ', 'Сума'] *= (1 + price_inc / 100)
df.loc[df['Тип'] == '2. ВИТРАТИ', 'Сума'] *= (1 - cost_red / 100)

df['Місяць'] = df['Дата'].dt.strftime('%m-%Y')

# Метрики
total_inc = df[df['Тип'] == '1. ДОХОДИ']['Сума'].sum()
total_exp = df[df['Тип'] == '2. ВИТРАТИ']['Сума'].sum()
profit = total_inc - total_exp
ros = (profit / total_inc * 100) if total_inc > 0 else 0

# 5. ВІДОБРАЖЕННЯ
st.title("Financial Strategy Dashboard")

# Ключові показники
c1, c2, c3 = st.columns(3)
c1.metric("Річний оборот", f"{total_inc:,.0f} PLN")
c2.metric("Чистий прибуток", f"{profit:,.0f} PLN")
c3.metric("Рентабельність (ROS)", f"{ros:.1f}%")

# 6. WATERFALL CHART
st.divider()
st.subheader("💎 Як формується прибуток")
exp_sum = df[df['Тип'] == '2. ВИТРАТИ'].groupby('Стаття')['Сума'].sum().sort_values(ascending=False)
fig_wf = go.Figure(go.Waterfall(
    measure = ["relative"] * (len(exp_sum) + 1) + ["total"],
    x = ["Виручка"] + list(exp_sum.index) + ["Прибуток"],
    y = [total_inc] + [-v for v in exp_sum.values] + [0],
    textposition = "outside",
    connector = {"line":{"color":"rgba(63, 63, 63, 0.5)"}},
))
st.plotly_chart(fig_wf, use_container_width=True)

# 7. КРУГОВІ ДІАГРАМИ
st.divider()
st.subheader("📊 Структура витрат: Порівняння")
cp1, cp2 = st.columns(2)
for i, col in enumerate([cp1, cp2]):
    m_val = 1 if i == 0 else 12
    p_data = df[(df['Тип'] == '2. ВИТРАТИ') & (df['Дата'].dt.month == m_val)]
    fig = go.Figure(data=[go.Pie(labels=p_data['Стаття'], values=p_data['Сума'], hole=.4)])
    fig.update_layout(title="Січень (Початок року)" if i == 0 else "Грудень (Прогноз)", height=400)
    col.plotly_chart(fig, use_container_width=True)

# 8. ТАБЛИЦЯ P&L (ВИПРАВЛЕНИЙ ПІВОТ)
st.divider()
st.subheader("📑 Звіт P&L за місяцями")

# ТУТ ВИПРАВЛЕНО: values='Сума', а не 'Sum'
pnl = df.pivot_table(
    index=['Тип', 'Стаття'], 
    columns='Місяць', 
    values='Сума', 
    aggfunc='sum'
)

# Сортуємо місяці хронологічно
month_order = sorted(df['Місяць'].unique(), key=lambda x: pd.to_datetime(x, format='%m-%Y'))
pnl = pnl[month_order]

st.dataframe(
    pnl.style.format("{:,.0f}")
    .background_gradient(cmap='Greens', subset=pd.IndexSlice[('1. ДОХОДИ', slice(None)), :])
    .background_gradient(cmap='Reds', subset=pd.IndexSlice[('2. ВИТРАТИ', slice(None)), :]),
    use_container_width=True
)

# 9. CASH FLOW
st.divider()
st.subheader("📉 Прогноз руху коштів (Cash Flow)")
df['Зміна'] = df.apply(lambda x: x['Сума'] if 'ДОХОДИ' in x['Тип'] else -x['Сума'], axis=1)
daily_cf = df.groupby('Дата')['Зміна'].sum().reset_index()
daily_cf['Залишок'] = init_bal + daily_cf['Зміна'].cumsum()

fig_cf = go.Figure()
fig_cf.add_trace(go.Scatter(x=daily_cf['Дата'], y=daily_cf['Залишок'], fill='tozeroy', line_color='#00CC96', name="Баланс"))
fig_cf.add_hline(y=0, line_dash="dash", line_color="red")
st.plotly_chart(fig_cf, use_container_width=True)

if daily_cf['Залишок'].min() < 0:
    st.error(f"🚨 Касовий розрив: {abs(daily_cf['Залишок'].min()):,.0f} PLN. Бізнесу знадобляться додаткові кошти.")
else:
    st.success("✅ Фінансова модель стійка.")
