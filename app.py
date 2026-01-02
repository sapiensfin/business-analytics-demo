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
    
    # Базові витрати (оптимізовані, щоб був прибуток)
    expense_categories = {
        'Зарплата водії': 180000,
        'Паливо (ПММ)': 95000,
        'Лізинг авто': 70000,
        'Зарплата офіс': 55000,
        'Податки': 45000,
        'Оренда та склад': 40000,
        'Ремонт та сервіс': 20000,
        'Маркетинг': 15000,
        'Амортизація': 10000
    }

    for month in months:
        m_num = month.month
        rev_f = 0.7 if m_num in [3, 10] else 1.0 # Сезонність
        dynamic_f = 1.0 + (m_num * 0.01) # Легкий ріст витрат
        
        # Дохід
        data.append({'Date': month, 'Type': '1. ПРИХОДИ', 'Category': 'Виручка B2B', 'Amount': 550000.0 * rev_f})
        
        # Витрати
        for cat, amt in expense_categories.items():
            val = amt * dynamic_f
            if cat == 'Ремонт та сервіс' and m_num in [3, 10]: val *= 2.5
            data.append({'Date': month, 'Type': '2. ВИТРАТИ', 'Category': cat, 'Amount': float(val)})
            
    return pd.DataFrame(data)

# 3. БІЧНА ПАНЕЛЬ
with st.sidebar:
    st.header("🕹️ Симулятор рішень")
    price_inc = st.slider("Збільшення цін (%)", 0, 50, 5) # По замовчуванню +5%
    cost_red = st.slider("Оптимізація витрат (%)", 0, 50, 10) # По замовчуванню 10%
    st.write("---")
    st.markdown("### Обговорити ваш проєкт")
    st.link_button("🤝 Зв'язатися з експертом", "https://sapiensfin.eu")

# 4. ОБРОБКА ДАНИХ
df = get_base_data().copy()
df.loc[df['Type'] == '1. ПРИХОДИ', 'Amount'] *= (1 + price_inc / 100)
df.loc[df['Type'] == '2. ВИТРАТИ', 'Amount'] *= (1 - cost_red / 100)
df['Month_Year'] = df['Date'].dt.strftime('%m-%Y')

# Розрахунок підсумків
total_inc = df[df['Type'] == '1. ПРИХОДИ']['Amount'].sum()
total_exp_df = df[df['Type'] == '2. ВИТРАТИ'].groupby('Category')['Amount'].sum().sort_values(ascending=False)
total_exp_sum = total_exp_df.sum()
net_profit = total_inc - total_exp_sum

# 5. МЕТРИКИ
st.title("Financial Strategy Dashboard")
m1, m2, m3 = st.columns(3)
m1.metric("Річний оборот", f"{total_inc:,.0f} PLN")
m2.metric("Чистий прибуток", f"{net_profit:,.0f} PLN", delta=f"{(net_profit/total_inc*100):.1f}% ROS")
m3.metric("Всього витрат", f"{total_exp_sum:,.0f} PLN")

# 6. WATERFALL CHART (ВИПРАВЛЕНА МАТЕМАТИКА)
st.divider()
st.subheader("💎 Математика прибутку: Waterfall")

# Формуємо списки для графіка
x_labels = ["Виручка"] + list(total_exp_df.index) + ["Чистий прибуток"]
y_values = [total_inc] + [-v for v in total_exp_df.values] + [net_profit]
# Measure: 'relative' для всіх, 'absolute' для останнього стовпчика (це і є фікс)
measures = ["relative"] * (len(total_exp_df) + 1) + ["absolute"]

fig_wf = go.Figure(go.Waterfall(
    measure = measures,
    x = x_labels,
    y = y_values,
    base = 0,
    text = [f"{v:,.0f}" for v in y_values],
    textposition = "outside",
    connector = {"line":{"color":"rgba(63, 63, 63, 0.5)"}},
    increasing = {"marker":{"color":"#2ecc71"}},
    decreasing = {"marker":{"color":"#e74c3c"}},
    totals = {"marker":{"color":"#3498db" if net_profit > 0 else "#e74c3c"}}
))

fig_wf.update_layout(height=550, showlegend=False, margin=dict(t=50, b=50))
st.plotly_chart(fig_wf, use_container_width=True)

# 7. ТАБЛИЦЯ P&L З ПРИБУТКОМ
st.divider()
st.subheader("📑 Детальний звіт P&L")

pnl = df.pivot_table(index=['Type', 'Category'], columns='Month_Year', values='Amount', aggfunc='sum')
cols_sorted = sorted(df['Month_Year'].unique(), key=lambda x: pd.to_datetime(x, format='%m-%Y'))
pnl = pnl[cols_sorted]

# Додаємо рядок прибутку
profit_row = pnl.loc['1. ПРИХОДИ'].sum() - pnl.loc['2. ВИТРАТИ'].sum()
profit_df = pd.DataFrame([profit_row], index=pd.MultiIndex.from_tuples([('3. РЕЗУЛЬТАТ', 'ЧИСТИЙ ПРИБУТОК')]))
profit_df.columns = pnl.columns
pnl_final = pd.concat([pnl, profit_df])

st.dataframe(
    pnl_final.style.format("{:,.0f}")
    .background_gradient(cmap='GnBu', subset=pd.IndexSlice[('1. ПРИХОДИ', slice(None)), :])
    .background_gradient(cmap='YlOrRd', subset=pd.IndexSlice[('2. ВИТРАТИ', slice(None)), :])
    .apply(lambda x: ['background-color: #3498db; color: white' if x.name[0] == '3. РЕЗУЛЬТАТ' else '' for _ in x], axis=1),
    use_container_width=True
)

# 8. КРУГОВІ ДІАГРАМИ
st.divider()
st.subheader("📊 Структура витрат: Порівняння")
c_p1, c_p2 = st.columns(2)
for i, col in enumerate([c_p1, c_p2]):
    m_target = 1 if i == 0 else 12
    pie_data = df[(df['Type'] == '2. ВИТРАТИ') & (df['Date'].dt.month == m_target)]
    fig = go.Figure(data=[go.Pie(labels=pie_data['Category'], values=pie_data['Amount'], hole=.4)])
    fig.update_layout(title="Січень" if i == 0 else "Грудень", height=400)
    col.plotly_chart(fig, use_container_width=True)
