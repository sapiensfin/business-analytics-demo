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
        rev_f = 0.7 if m_num in [3, 10] else 1.0 
        dynamic_f = 1.0 + (m_num * 0.015) # Посилений ріст для різниці в діаграмах
        
        # Дохід
        data.append({'Date': month, 'Type': '1. ПРИХОДИ', 'Category': 'Виручка B2B', 'Amount': 580000.0 * rev_f})
        
        # Витрати
        for cat, amt in expense_categories.items():
            val = amt * dynamic_f
            if cat == 'Ремонт та сервіс' and m_num in [3, 10]: val *= 2.8
            data.append({'Date': month, 'Type': '2. ВИТРАТИ', 'Category': cat, 'Amount': float(val)})
            
    return pd.DataFrame(data)

# 3. БІЧНА ПАНЕЛЬ
with st.sidebar:
    st.header("🕹️ Симулятор рішень")
    price_inc = st.slider("Збільшення цін (%)", 0, 50, 5)
    cost_red = st.slider("Оптимізація витрат (%)", 0, 50, 10)
    st.write("---")
    init_bal = st.number_input("Обігові кошти на старті (PLN)", value=100000)
    st.write("---")
    st.link_button("🤝 Обговорити ваш проєкт", "https://sapiensfin.eu", use_container_width=True)

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

# 6. WATERFALL CHART (Математично точний)
st.divider()
st.subheader("💎 Математика прибутку: Waterfall")

x_labels = ["Виручка"] + list(total_exp_df.index) + ["Чистий прибуток"]
y_values = [total_inc] + [-v for v in total_exp_df.values] + [net_profit]
measures = ["relative"] * (len(total_exp_df) + 1) + ["absolute"]

fig_wf = go.Figure(go.Waterfall(
    measure = measures,
    x = x_labels,
    y = y_values,
    text = [f"{v:,.0f}" for v in y_values],
    textposition = "outside",
    connector = {"line":{"color":"rgba(63, 63, 63, 0.5)"}},
    increasing = {"marker":{"color":"#2ecc71"}},
    decreasing = {"marker":{"color":"#e74c3c"}},
    totals = {"marker":{"color":"#3498db" if net_profit > 0 else "#e74c3c"}}
))
fig_wf.update_layout(height=500)
st.plotly_chart(fig_wf, use_container_width=True)

# 7. КРУГОВІ ДІАГРАМИ
st.divider()
st.subheader("📊 Структура витрат: Порівняння")
c_p1, c_p2 = st.columns(2)
for i, col in enumerate([c_p1, c_p2]):
    m_target = 1 if i == 0 else 12
    pie_data = df[(df['Type'] == '2. ВИТРАТИ') & (df['Date'].dt.month == m_target)]
    fig = go.Figure(data=[go.Pie(labels=pie_data['Category'], values=pie_data['Amount'], hole=.4)])
    fig.update_layout(title="Січень (Старт)" if i == 0 else "Грудень (Прогноз)", height=400)
    col.plotly_chart(fig, use_container_width=True)

# 8. ТАБЛИЦЯ P&L
st.divider()
st.subheader("📑 Детальний звіт P&L за місяцями")
pnl = df.pivot_table(index=['Type', 'Category'], columns='Month_Year', values='Amount', aggfunc='sum')
cols_sorted = sorted(df['Month_Year'].unique(), key=lambda x: pd.to_datetime(x, format='%m-%Y'))
pnl = pnl[cols_sorted]

profit_row = pnl.loc['1. ПРИХОДИ'].sum() - pnl.loc['2. ВИТРАТИ'].sum()
profit_df = pd.DataFrame([profit_row], index=pd.MultiIndex.from_tuples([('3. РЕЗУЛЬТАТ', 'ЧИСТИЙ ПРИБУТОК')]))
profit_df.columns = pnl.columns
pnl_final = pd.concat([pnl, profit_df])

st.dataframe(
    pnl_final.style.format("{:,.0f}")
    .background_gradient(cmap='GnBu', subset=pd.IndexSlice[('1. ПРИХОДИ', slice(None)), :])
    .background_gradient(cmap='YlOrRd', subset=pd.IndexSlice[('2. ВИТРАТИ', slice(None)), :])
    .apply(lambda x: ['background-color: #3498db; color: white; font-weight: bold' if x.name[0] == '3. РЕЗУЛЬТАТ' else '' for _ in x], axis=1),
    use_container_width=True
)

# 9. CASH FLOW (ПОВЕРНУТО)
st.divider()
st.subheader("📉 Прогноз руху грошових коштів (Cash Flow)")

# Розрахунок чистих грошових потоків за місяць
df['Net_Flow'] = df.apply(lambda x: x['Amount'] if 'ПРИХОДИ' in x['Type'] else -x['Amount'], axis=1)
cf_monthly = df.groupby('Date')['Net_Flow'].sum().reset_index()
cf_monthly['Cumulative_Cash'] = init_bal + cf_monthly['Net_Flow'].cumsum()

fig_cf = go.Figure()
fig_cf.add_trace(go.Scatter(
    x=cf_monthly['Date'], 
    y=cf_monthly['Cumulative_Cash'], 
    mode='lines+markers',
    fill='tozeroy',
    line=dict(color='#2E86C1', width=3),
    name="Залишок на рахунку"
))

# Додаємо лінію нуля (небезпечна зона)
fig_cf.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="Касовий розрив")

fig_cf.update_layout(
    xaxis_title="Місяць",
    yaxis_title="PLN",
    height=450,
    hovermode="x unified"
)
st.plotly_chart(fig_cf, use_container_width=True)

# Повідомлення про стан кешу
if cf_monthly['Cumulative_Cash'].min() < 0:
    st.error(f"⚠️ Увага! Можливий касовий розрив у розмірі {abs(cf_monthly['Cumulative_Cash'].min()):,.0f} PLN. Бізнесу знадобиться дофінансування.")
else:
    st.success("✅ Грошовий потік позитивний. Обігових коштів достатньо для покриття витрат.")
