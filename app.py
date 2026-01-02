import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Налаштування сторінки
st.set_page_config(page_title="SapiensFin | Professional Demo", layout="wide")

# 2. ГЕНЕРАЦІЯ ДАНИХ (Використовуємо латиницю для стабільності)
@st.cache_data
def get_base_data():
    data = []
    months = pd.date_range(start="2025-01-01", periods=12, freq='MS')
    
    expense_categories = {
        'Rent & Warehouse': 55000,
        'Office Salary': 65000,
        'Drivers Salary': 180000,
        'Fuel': 95000,
        'Leasing': 75000,
        'Repairs & Service': 25000,
        'Marketing': 20000,
        'Taxes': 55000,
        'Depreciation': 10000
    }

    for month in months:
        m_num = month.month
        rev_f = 0.6 if m_num in [3, 10] else 1.0
        rep_f = 3.5 if m_num in [3, 10] else 1.0
        
        # Дохід
        data.append({'Date': month, 'Type': 'Income', 'Category': 'B2B Revenue', 'Amount': 600000.0 * rev_f})
        
        # Витрати
        for cat, amt in expense_categories.items():
            val = amt * rep_f if cat == 'Repairs & Service' else amt
            data.append({'Date': month, 'Type': 'Expense', 'Category': cat, 'Amount': float(val)})
            
    return pd.DataFrame(data)

# 3. БІЧНА ПАНЕЛЬ
with st.sidebar:
    st.header("🕹️ Симулятор")
    price_inc = st.slider("Збільшення цін (%)", 0, 50, 0)
    cost_red = st.slider("Оптимізація витрат (%)", 0, 50, 0)
    init_bal = st.number_input("Стартовий капітал (PLN)", value=100000)

# 4. ОБРОБКА
df_base = get_base_data()
df = df_base.copy()

# Застосовуємо зміни
df.loc[df['Type'] == 'Income', 'Amount'] *= (1 + price_inc / 100)
df.loc[df['Type'] == 'Expense', 'Amount'] *= (1 - cost_red / 100)

df['Month_Year'] = df['Date'].dt.strftime('%m-%Y')

# Розрахунок метрик
total_inc = df[df['Type'] == 'Income']['Amount'].sum()
total_exp = df[df['Type'] == 'Expense']['Amount'].sum()
profit = total_inc - total_exp
ros = (profit / total_inc * 100) if total_inc > 0 else 0

# 5. ВІДОБРАЖЕННЯ МЕТРИК
st.title("Financial Strategy Dashboard")
c1, c2, c3 = st.columns(3)
c1.metric("Річний оборот", f"{total_inc:,.0f} PLN")
c2.metric("Чистий прибуток", f"{profit:,.0f} PLN")
c3.metric("Рентабельність (ROS)", f"{ros:.1f}%")

# 6. WATERFALL CHART
st.subheader("💎 Формування прибутку")
exp_summary = df[df['Type'] == 'Expense'].groupby('Category')['Amount'].sum().sort_values(ascending=False)
fig_wf = go.Figure(go.Waterfall(
    measure = ["relative"] * (len(exp_summary) + 1) + ["total"],
    x = ["Виручка"] + list(exp_summary.index) + ["Прибуток"],
    y = [total_inc] + [-v for v in exp_summary.values] + [0],
))
st.plotly_chart(fig_wf, use_container_width=True)

# 7. КРУГОВІ ДІАГРАМИ
st.divider()
st.subheader("📊 Структура витрат: Початок vs Кінець року")
cp1, cp2 = st.columns(2)
for i, col in enumerate([cp1, cp2]):
    m = 1 if i == 0 else 12
    p_data = df[(df['Type'] == 'Expense') & (df['Date'].dt.month == m)]
    fig = go.Figure(data=[go.Pie(labels=p_data['Category'], values=p_data['Amount'], hole=.4)])
    fig.update_layout(title="Січень" if i == 0 else "Грудень")
    col.plotly_chart(fig, use_container_width=True)

# 8. ТАБЛИЦЯ P&L (БЕЗПЕЧНИЙ ПІВОТ)
st.divider()
st.subheader("📑 Звіт P&L")

# Створюємо півот таблицю
# Використовуємо назви колонок, які ТОЧНО є в DF: 'Type', 'Category', 'Month_Year', 'Amount'
pnl = df.pivot_table(
    index=['Type', 'Category'], 
    columns='Month_Year', 
    values='Amount', 
    aggfunc='sum'
)

# Сортуємо колонки по датах
cols_sorted = sorted(df['Month_Year'].unique(), key=lambda x: pd.to_datetime(x, format='%m-%Y'))
pnl = pnl[cols_sorted]

# Відображення
st.dataframe(pnl.style.format("{:,.0f}").background_gradient(cmap='RdYlGn'), use_container_width=True)

# 9. CASH FLOW
st.divider()
st.subheader("📉 Прогноз Cash Flow")
df['Change'] = df.apply(lambda x: x['Amount'] if x['Type'] == 'Income' else -x['Amount'], axis=1)
cf_data = df.groupby('Date')['Change'].sum().reset_index()
cf_data['Balance'] = init_bal + cf_data['Change'].cumsum()

fig_cf = go.Figure()
fig_cf.add_trace(go.Scatter(x=cf_data['Date'], y=cf_data['Balance'], fill='tozeroy', line_color='#00CC96'))
st.plotly_chart(fig_cf, use_container_width=True)

if cf_data['Balance'].min() < 0:
    st.error(f"🚨 Касовий розрив: {abs(cf_data['Balance'].min()):,.0f} PLN")
else:
    st.success("✅ Модель стійка")
