import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Налаштування сторінки
st.set_page_config(page_title="SapiensFin | Professional Demo", layout="wide")

# --- 1. ГЕНЕРАЦІЯ ДАНИХ ---
@st.cache_data
def get_base_data():
    data = []
    # Створюємо дати для всього 2025 року
    months = pd.date_range(start="2025-01-01", periods=12, freq='MS')
    
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
        # Сезонність: у березні (3) та жовтні (10) дохід падає, витрати на ремонт ростуть
        rev_f = 0.6 if m_num in [3, 10] else 1.0
        rep_f = 3.5 if m_num in [3, 10] else 1.0
        
        data.append({'Дата': month, 'Тип': '1. ПРИХОДИ', 'Стаття': 'Виручка (B2B)', 'Сума': 600000 * rev_f})
        
        for cat, amt in expense_categories.items():
            val = amt * rep_f if cat == 'Ремонт та сервіс' else amt
            data.append({'Дата': month, 'Тип': '2. ВИТРАТИ', 'Стаття': cat, 'Сума': val})
            
    return pd.DataFrame(data)

# --- 2. БІЧНА ПАНЕЛЬ ---
with st.sidebar:
    st.markdown("### 🚀 Sapiens Fin")
    st.write("---")
    st.header("🕹️ Симулятор рішень")
    price_inc = st.slider("Збільшення цін (%)", 0, 50, 0)
    cost_red = st.slider("Оптимізація витрат (%)", 0, 50, 0)
    init_bal = st.number_input("Стартовий капітал (PLN)", value=100000)
    st.write("---")
    st.info("Змінюйте повзунки, щоб побачити вплив на прибуток та Cash Flow.")

# --- 3. ОБРОБКА ДАНИХ ---
df_base = get_base_data()
df = df_base.copy()

# Розрахунок дельти для метрик
base_inc = df_base[df_base['Тип'] == '1. ПРИХОДИ']['Сума'].sum()
base_prof = base_inc - df_base[df_base['Тип'] == '2. ВИТРАТИ']['Сума'].sum()

# Застосування симуляції
df.loc[df['Тип'] == '1. ПРИХОДИ', 'Сума'] *= (1 + price_inc / 100)
df.loc[df['Тип'] == '2. ВИТРАТИ', 'Сума'] *= (1 - cost_red / 100)

df['Місяць_Назва'] = df['Дата'].dt.strftime('%m-%Y')

# Метрики
inc_total = df[df['Тип'] == '1. ПРИХОДИ']['Сума'].sum()
exp_total = df[df['Тип'] == '2. ВИТРАТИ']['Сума'].sum()
net_prof = inc_total - exp_total
ros = (net_prof / inc_total * 100) if inc_total > 0 else 0

# --- 4. ГОЛОВНИЙ ЕКРАН ---
st.title("Financial Strategy Dashboard")

# Метрики з порівнянням
m1, m2, m3 = st.columns(3)
m1.metric("Річний оборот", f"{inc_total:,.0f} PLN", f"{inc_total - base_inc:,.0f}")
m2.metric("Чистий прибуток", f"{net_prof:,.0f} PLN", f"{net_prof - base_prof:,.0f}")
m3.metric("Рентабельність (ROS)", f"{ros:.1f}%", f"{ros - (base_prof/base_inc*100):.1f}%")

# --- 5. WATERFALL CHART ---
st.divider()
st.subheader("💎 Як формується прибуток (Waterfall)")
exp_by_cat = df[df['Тип'] == '2. ВИТРАТИ'].groupby('Стаття')['Сума'].sum().sort_values(ascending=False)

fig_wf = go.Figure(go.Waterfall(
    measure = ["relative"] * (len(exp_by_cat) + 1) + ["total"],
    x = ["Виручка"] + list(exp_by_cat.index) + ["Чистий прибуток"],
    y = [inc_total] + [-v for v in exp_by_cat.values] + [0],
    connector = {"line":{"color":"rgba(63, 63, 63, 0.5)"}},
))
st.plotly_chart(fig_wf, use_container_width=True)

# --- 6. КРУГОВІ ДІАГРАМИ (СТРУКТУРА ВИТРАТ) ---
st.divider()
st.subheader("📊 Структура витрат: Порівняння")
c_pie1, c_pie2 = st.columns(2)

for i, col in enumerate([c_pie1, c_pie2]):
    m_target = 1 if i == 0 else 12
    title = "Січень (Старт)" if i == 0 else "Грудень (Прогноз)"
    pie_data = df[(df['Тип'] == '2. ВИТРАТИ') & (df['Дата'].dt.month == m_target)]
    fig = go.Figure(data=[go.Pie(labels=pie_data['Стаття'], values=pie_data['Сума'], hole=.4)])
    fig.update_layout(title=title, height=380, margin=dict(t=50, b=0, l=0, r=0))
    col.plotly_chart(fig, use_container_width=True)

# --- 7. ТАБЛИЦЯ P&L (З ВИПРАВЛЕНОЮ ПОМИЛКОЮ) ---
st.divider()
st.subheader("📑 Звіт про прибутки та збитки (P&L)")
# Виправлено: values='Сума' (відповідає назві в DataFrame)
pnl = df.pivot_table(index=['Тип', 'Стаття'], columns='Місяць_Назва', values='Сума', aggfunc='sum', sort=False)
# Гарантуємо правильний порядок місяців
months_order = df.sort_values('Дата')['Місяць_Назва'].unique()
pnl = pnl[months_order]

st.dataframe(
    pnl.style.format("{:,.0f}")
    .background_gradient(cmap='Greens', subset=pd.IndexSlice[('1. ПРИХОДИ', slice(None)), :])
    .background_gradient(cmap='Reds', subset=pd.IndexSlice[('2. ВИТРАТИ', slice(None)), :]),
    use_container_width=True
)

# --- 8. CASH FLOW ГРАФІК ---
st.divider()
st.subheader("📉 Прогноз залишку грошових коштів")
df_cf = df.sort_values('Дата').copy()
df_cf['Різниця'] = df_cf.apply(lambda x: x['Сума'] if 'ПРИХОДИ' in x['Тип'] else -x['Сума'], axis=1)
cf_daily = df_cf.groupby('Дата')['Різниця'].sum().reset_index()
cf_daily['Залишок'] = init_bal + cf_daily['Різниця'].cumsum()

fig_cf = go.Figure()
fig_cf.add_trace(go.Scatter(x=cf_daily['Дата'], y=cf_daily['Залишок'], mode='lines', fill='tozeroy', line=dict(color='#00CC96')))
fig_cf.add_hline(y=0, line_dash="dash", line_color="red")
st.plotly_chart(fig_cf, use_container_width=True)

if cf_daily['Залишок'].min() < 0:
    st.error(f"⚠️ Ризик касового розриву! Мінімальний баланс: {cf_daily['Залишок'].min():,.0f} PLN")
else:
    st.success("✅ Фінансова модель стійка.")
