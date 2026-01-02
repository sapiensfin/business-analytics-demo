import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# 1. Налаштування сторінки
st.set_page_config(page_title="SapiensFin | Professional Demo", layout="wide")

# 2. ГЕНЕРАЦІЯ ДАНИХ
@st.cache_data
def get_base_data():
    data = []
    months = pd.date_range(start="2025-01-01", periods=12, freq='MS')
    
    expense_categories = {
        'Оренда та склад': 55000,
        'Зарплата офіс': 65000,
        'Зарплата водії': 180000,
        'Паливо (ПММ)': 95000,
        'Лізинг авто': 75000,
        'Ремонт та сервіс': 25000,
        'Маркетинг': 20000,
        'Податки': 55000,
        'Амортизація': 10000
    }

    for month in months:
        m_num = month.month
        # Сезонність
        rev_f = 0.6 if m_num in [3, 10] else 1.0
        rep_f = 3.5 if m_num in [3, 10] else 1.0
        # Додаємо невеликий ріст витрат до кінця року для візуальної різниці в Pie Chart
        growth_f = 1 + (m_num * 0.02) 
        
        # Дохід
        data.append({'Date': month, 'Type': '1. ПРИХОДИ', 'Category': 'Виручка B2B', 'Amount': 600000.0 * rev_f})
        
        # Витрати
        for cat, amt in expense_categories.items():
            val = amt
            if cat == 'Ремонт та сервіс': 
                val *= rep_f
            else:
                val *= growth_f # Витрати трохи змінюються щомісяця
            
            data.append({'Date': month, 'Type': '2. ВИТРАТИ', 'Category': cat, 'Amount': float(val)})
            
    return pd.DataFrame(data)

# 3. БІЧНА ПАНЕЛЬ
with st.sidebar:
    st.image("https://via.placeholder.com/150x50?text=Sapiens+Fin", use_container_width=True)
    st.header("🕹️ Симулятор")
    price_inc = st.slider("Збільшення ціни (%)", 0, 50, 0)
    cost_red = st.slider("Оптимізація витрат (%)", 0, 50, 0)
    st.write("---")
    init_bal = st.number_input("Обігові кошти на старті (PLN)", value=50000)
    st.caption("Налаштуйте параметри, щоб побачити прогноз.")

# 4. ОБРОБКА
df_base = get_base_data()
df = df_base.copy()

df.loc[df['Type'] == '1. ПРИХОДИ', 'Amount'] *= (1 + price_inc / 100)
df.loc[df['Type'] == '2. ВИТРАТИ', 'Amount'] *= (1 - cost_red / 100)
df['Month_Year'] = df['Date'].dt.strftime('%m-%Y')

# Метрики
total_inc = df[df['Type'] == '1. ПРИХОДИ']['Amount'].sum()
total_exp = df[df['Type'] == '2. ВИТРАТИ']['Amount'].sum()
profit = total_inc - total_exp
ros = (profit / total_inc * 100) if total_inc > 0 else 0

# 5. ВІДОБРАЖЕННЯ
st.title("Financial Strategy Dashboard")
c1, c2, c3 = st.columns(3)
c1.metric("Річний оборот", f"{total_inc:,.0f} PLN")
c2.metric("Чистий прибуток", f"{profit:,.0f} PLN")
c3.metric("Рентабельність (ROS)", f"{ros:.1f}%")

# 6. WATERFALL CHART
st.subheader("💎 Структура формування прибутку")
exp_summary = df[df['Type'] == '2. ВИТРАТИ'].groupby('Category')['Amount'].sum().sort_values(ascending=False)
fig_wf = go.Figure(go.Waterfall(
    measure = ["relative"] * (len(exp_summary) + 1) + ["total"],
    x = ["Виручка"] + list(exp_summary.index) + ["Чистий прибуток"],
    y = [total_inc] + [-v for v in exp_summary.values] + [0],
    textposition = "outside",
    connector = {"line":{"color":"rgba(63, 63, 63, 0.5)"}},
))
fig_wf.update_layout(height=450)
st.plotly_chart(fig_wf, use_container_width=True)

# 7. КРУГОВІ ДІАГРАМИ (З РІЗНИМИ ДАНИМИ)
st.divider()
st.subheader("📊 Зміна структури витрат: Січень vs Грудень")
cp1, cp2 = st.columns(2)
for i, col in enumerate([cp1, cp2]):
    m_num = 1 if i == 0 else 12
    p_data = df[(df['Type'] == '2. ВИТРАТИ') & (df['Date'].dt.month == m_num)]
    fig = go.Figure(data=[go.Pie(labels=p_data['Category'], values=p_data['Amount'], hole=.4)])
    fig.update_layout(title="Січень (Початок)" if i == 0 else "Грудень (Кінець року)", height=400)
    col.plotly_chart(fig, use_container_width=True)

# 8. ТАБЛИЦЯ P&L (КОЛЬОРИ ЯК У ПОЧАТКОВОМУ ВАРІАНТІ)
st.divider()
st.subheader("📑 Річний звіт P&L")

pnl = df.pivot_table(index=['Type', 'Category'], columns='Month_Year', values='Amount', aggfunc='sum')
cols_sorted = sorted(df['Month_Year'].unique(), key=lambda x: pd.to_datetime(x, format='%m-%Y'))
pnl = pnl[cols_sorted]

# Стілізація
st.dataframe(
    pnl.style.format("{:,.0f}")
    .background_gradient(cmap='GnBu', subset=pd.IndexSlice[('1. ПРИХОДИ', slice(None)), :])
    .background_gradient(cmap='YlOrRd', subset=pd.IndexSlice[('2. ВИТРАТИ', slice(None)), :]), 
    use_container_width=True
)

# 9. CASH FLOW
st.divider()
st.subheader("📉 Прогноз руху грошових коштів (Cash Flow)")
df['Change'] = df.apply(lambda x: x['Amount'] if x['Type'] == '1. ПРИХОДИ' else -x['Amount'], axis=1)
cf_data = df.groupby('Date')['Change'].sum().reset_index()
cf_data['Balance'] = init_bal + cf_data['Change'].cumsum()

fig_cf = go.Figure()
fig_cf.add_trace(go.Scatter(x=cf_data['Date'], y=cf_data['Balance'], fill='tozeroy', line_color='#2E86C1', name="Баланс"))
fig_cf.add_hline(y=0, line_dash="dash", line_color="red")
st.plotly_chart(fig_cf, use_container_width=True)

if cf_data['Balance'].min() < 0:
    st.error(f"🚨 Увага: Прогнозується касовий розрив {abs(cf_data['Balance'].min()):,.0f} PLN. Збільште обігові кошти або оптимізуйте виплати.")
else:
    st.success("✅ Фінансова стійкість підтверджена: касових розривів не виявлено.")
