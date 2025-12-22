import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Налаштування сторінки
st.set_page_config(page_title="Vitalii Ometsynskyi | BI & Automation", layout="wide")

# --- 1. ГЕНЕРАЦІЯ ДАНИХ (12 МІСЯЦІВ) ---
def get_extended_data():
    data = []
    months = [f"2025-{m:02d}" for m in range(1, 13)]
    
    expense_categories = {
        'Оренда та склад': 55000,
        'Зарплата офіс': 65000,
        'Зарплата водії': 180000,
        'Бонуси за KPI': 25000,
        'ПММ (Паливо)': 95000,
        'Лізинг авто': 70000,
        'Страхування (OC/AC)': 12000,
        'Ремонт та сервіс': 20000,
        'Маркетинг та реклама': 15000,
        'Комунальні (Media)': 8000,
        'Послуги бухгалтерії': 6000,
        'Податки на ФОП/ЗП': 55000,
        'Амортизація': 10000
    }

    for m in months:
        month_num = int(m.split('-')[1])
        seasonality = 1 + (month_num * 0.015)
        
        data.append({'Дата': f'{m}-05', 'Тип': '1. ПРИХОДИ', 'Стаття': 'Виручка (Рахунок)', 'Сума': 560000 * seasonality})
        data.append({'Дата': f'{m}-07', 'Тип': '1. ПРИХОДИ', 'Стаття': 'Виручка (Готівка)', 'Сума': 110000 * seasonality})
        
        for cat, amt in expense_categories.items():
            val = amt
            if cat == 'Ремонт та сервіс' and month_num in [3, 10]: val *= 3.5
            if cat == 'ПММ (Паливо)' and month_num in [7, 8]: val *= 1.2
            data.append({'Дата': f'{m}-15', 'Тип': '2. ВИТРАТИ', 'Стаття': cat, 'Сума': val})
            
    return pd.DataFrame(data)

# --- 2. БІЧНА ПАНЕЛЬ (ЕКСПЕРТНИЙ ПРОФІЛЬ) ---
with st.sidebar:
    st.title("Віталій Омецинський")
    st.markdown("**Business & Process Analyst**")
    st.write("Спеціалізація: Логістика, Ритейл, AI-автоматизація[cite: 7, 12].")
    st.write("---")
    st.header("🕹️ What-If Симулятор")
    inc_change = st.slider("Зміна доходу (%)", -20, 40, 0)
    exp_opt = st.slider("Оптимізація витрат (%)", -30, 0, 0)
    init_bal = st.number_input("Початковий баланс (PLN)", value=150000)
    st.write("---")
    st.markdown(f"📧 {st.secrets.get('EMAIL', 'vitalii.ometsynskyi@gmail.com')}")
    st.markdown("[LinkedIn Profile](https://www.linkedin.com/in/witalio)")

# --- 3. ОБРОБКА ТА СИМУЛЯЦІЯ ---
df = get_extended_data()
df['Дата'] = pd.to_datetime(df['Дата'])
df['Сума'] = pd.to_numeric(df['Сума'])

df.loc[df['Тип'] == '1. ПРИХОДИ', 'Сума'] *= (1 + inc_change / 100)
df.loc[df['Тип'] == '2. ВИТРАТИ', 'Сума'] *= (1 + exp_opt / 100)

df['Місяць'] = df['Дата'].dt.strftime('%m-%Y')

# --- 4. КЛЮЧОВІ ПОКАЗНИКИ ---
st.title("🚀 Financial & Operational Strategy Simulator")
st.markdown("Гібридне рішення: Методологія IIBA + Python + AI[cite: 6, 31].")

income = df[df['Тип'] == '1. ПРИХОДИ'].groupby('Місяць', sort=False)['Сума'].sum()
expense = df[df['Тип'] == '2. ВИТРАТИ'].groupby('Місяць', sort=False)['Сума'].sum()
profit = income - expense
margin = (profit / income * 100)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Річна виручка", f"{income.sum():,.0f} PLN")
c2.metric("Чистий прибуток", f"{profit.sum():,.0f} PLN")
c3.metric("Рентабельність (avg)", f"{margin.mean():.1f}%")
c4.metric("EBITDA (Est.)", f"{(profit.sum() + 120000):,.0f} PLN")

# --- 5. ТАБЛИЦЯ P&L (ВИПРАВЛЕНА) ---
st.subheader("📑 Звіт про фінансові результати (P&L)")
pnl = df.pivot_table(index=['Тип', 'Стаття'], columns='Місяць', values='Сума', aggfunc='sum', sort=False)

# Виправлено: видалено параметр alpha
st.dataframe(
    pnl.style.format("{:,.0f}")
    .background_gradient(cmap='GnBu', subset=pd.IndexSlice[('1. ПРИХОДИ', slice(None)), :])
    .background_gradient(cmap='YlOrRd', subset=pd.IndexSlice[('2. ВИТРАТИ', slice(None)), :]),
    use_container_width=True
)

# --- 6. CASH FLOW ---
st.divider()
st.subheader("📉 Прогноз руху грошових коштів")

df = df.sort_values('Дата')
df['Зміна'] = df.apply(lambda x: x['Сума'] if 'ПРИХОДИ' in x['Тип'] else -x['Сума'], axis=1)
df['Залишок'] = init_bal + df['Зміна'].cumsum()

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=df['Дата'], y=df['Залишок'], 
    mode='lines', fill='tozeroy', 
    line=dict(color='#4A90E2', width=3),
    fillcolor='rgba(74, 144, 226, 0.1)'
))
fig.add_hline(y=0, line_dash="dash", line_color="#E74C3C")
fig.update_layout(xaxis_title="Період прогнозування", yaxis_title="Баланс (PLN)", height=450)
st.plotly_chart(fig, use_container_width=True)

if df['Залишок'].min() < 0:
    st.error(f"⚠️ Ризик касового розриву! Мінімальний залишок: {df['Залишок'].min():,.0f} PLN")
else:
    st.success("✅ Фінансова модель стійка при заданих параметрах.")
