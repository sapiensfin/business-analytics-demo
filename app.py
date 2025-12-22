import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Налаштування сторінки
st.set_page_config(page_title="Vitalii Ometsynskyi | Business Intelligence", layout="wide")

# --- 1. ГЕНЕРАЦІЯ РЕАЛІСТИЧНИХ ДАНИХ (12 МІСЯЦІВ) ---
def get_extended_data():
    data = []
    # Використовуємо кириличні назви для стабільності
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
        
        # Доходи
        data.append({'Дата': f'{m}-05', 'Тип': '1. ПРИХОДИ', 'Стаття': 'Виручка (Рахунок)', 'Сума': 560000 * seasonality})
        data.append({'Дата': f'{m}-07', 'Тип': '1. ПРИХОДИ', 'Стаття': 'Виручка (Готівка)', 'Сума': 110000 * seasonality})
        
        # Витрати
        for cat, amt in expense_categories.items():
            val = amt
            if cat == 'Ремонт та сервіс' and month_num in [3, 10]: val *= 3.5
            if cat == 'ПММ (Паливо)' and month_num in [7, 8]: val *= 1.2
            data.append({'Дата': f'{m}-15', 'Тип': '2. ВИТРАТИ', 'Стаття': cat, 'Сума': val})
            
    return pd.DataFrame(data)

# --- 2. БІЧНА ПАНЕЛЬ (КОНТАКТИ ТА КЕРУВАННЯ) ---
with st.sidebar:
    st.title("👨‍💼 Віталій Омецинський")
    st.info("Business Analyst | Python + AI [cite: 2, 6]")
    st.write("---")
    st.header("🕹️ What-If Симулятор")
    inc_change = st.slider("Зміна доходу (%)", -20, 40, 0)
    exp_opt = st.slider("Оптимізація витрат (%)", -30, 0, 0)
    init_bal = st.number_input("Початковий баланс (PLN)", value=150000)
    st.write("---")
    st.markdown("[LinkedIn Profile](www.linkedin.com/in/witalio) [cite: 3]")

# --- 3. ОБРОБКА ДАНИХ ---
df = get_extended_data()
df['Дата'] = pd.to_datetime(df['Дата'])
df['Сума'] = pd.to_numeric(df['Сума'])

# Застосування симуляції
df.loc[df['Тип'] == '1. ПРИХОДИ', 'Сума'] *= (1 + inc_change / 100)
df.loc[df['Тип'] == '2. ВИТРАТИ', 'Сума'] *= (1 + exp_opt / 100)

df['Місяць'] = df['Дата'].dt.strftime('%m-%Y')

# --- 4. DASHBOARD ---
st.title("🚀 Стратегічний фінансовий симулятор")
st.markdown("Поєднання методології IIBA з Python-аналітикою для вашого бізнесу[cite: 6, 31].")

# Рентабельність
income = df[df['Тип'] == '1. ПРИХОДИ'].groupby('Місяць', sort=False)['Сума'].sum()
expense = df[df['Тип'] == '2. ВИТРАТИ'].groupby('Місяць', sort=False)['Сума'].sum()
profit = income - expense
margin = (profit / income * 100)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Річна виручка", f"{income.sum():,.0f} PLN")
c2.metric("Чистий прибуток", f"{profit.sum():,.0f} PLN")
c3.metric("Маржинальність (avg)", f"{margin.mean():.1f}%")
c4.metric("EBITDA", f"{(profit.sum() + 120000):,.0f} PLN")

# --- 5. P&L ТАБЛИЦЯ (СПОКІЙНІ КОЛЬОРИ) ---
st.subheader("📑 Звіт про прибутки та збитки (P&L)")
pnl = df.pivot_table(index=['Тип', 'Стаття'], columns='Місяць', values='Сума', aggfunc='sum', sort=False)

# Використовуємо пастельну гаму: 'YlGn' (жовто-зелений) та 'BuPu' (блакитно-пурпурний)
st.dataframe(
    pnl.style.format("{:,.0f}")
    .background_gradient(cmap='GnBu', subset=pd.IndexSlice[('1. ПРИХОДИ', slice(None)), :])
    .background_gradient(cmap='YlOrRd', subset=pd.IndexSlice[('2. ВИТРАТИ', slice(None)), :], alpha=0.3),
    use_container_width=True
)

# --- 6. CASH FLOW ГРАФІК ---
st.divider()
st.subheader("📉 Динаміка капіталу (Cash Flow)")

df = df.sort_values('Дата')
# ВИПРАВЛЕНО: Тільки кириличні назви колонок
df['Зміна'] = df.apply(lambda x: x['Сума'] if 'ПРИХОДИ' in x['Тип'] else -x['Сума'], axis=1)
df['Залишок'] = init_bal + df['Зміна'].cumsum()

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=df['Дата'], y=df['Залишок'], 
    mode='lines', 
    fill='tozeroy', 
    name='Залишок', 
    line=dict(color='#4A90E2', width=3), # Професійний синій
    fillcolor='rgba(74, 144, 226, 0.1)'
))
fig.add_hline(y=0, line_dash="dash", line_color="#E74C3C")
fig.update_layout(xaxis_title="Прогноз на рік", yaxis_title="PLN", height=450)
st.plotly_chart(fig, use_container_width=True)

if df['Залишок'].min() < 0:
    st.error(f"⚠️ Ризик касового розриву: {df['Залишок'].min():,.0f} PLN. Необхідна корекція моделі.")
