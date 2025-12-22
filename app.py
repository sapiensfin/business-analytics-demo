import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(page_title="Financial Architect Demo", layout="wide")

# --- ФУНКЦІЯ ГЕНЕРАЦІЇ ДЕМО-ДАНИХ ---
def get_demo_data():
    months = pd.date_range(start='2024-01-01', periods=12, freq='M')
    categories = ['Оренда', 'Зарплата офіс', 'Зарплата склад', 'Зарплата водії', 
                  'Ремонт а/м', 'ПММ', 'Офіс', 'Бухгалтерія', 'Комунальні', 'Податки']
    
    data = []
    for month in months:
        # Приходи
        income_cash = np.random.randint(200000, 300000)
        income_bank = np.random.randint(400000, 600000)
        
        # Витрати (фіксовані + рандом)
        expenses = {
            'Оренда': 50000, 'Зарплата офіс': 80000, 'Зарплата склад': 120000,
            'Зарплата водії': 150000, 'Ремонт а/м': np.random.randint(10000, 40000),
            'ПММ': np.random.randint(60000, 100000), 'Офіс': 5000, 
            'Бухгалтерія': 10000, 'Комунальні': 15000, 'Податки': 70000
        }
        
        row = {'Дата': month, 'Прихід Готівка': income_cash, 'Прихід Рахунок': income_bank}
        row.update(expenses)
        data.append(row)
    
    return pd.DataFrame(data)

# --- ІНТЕРФЕЙС ---
st.title("📊 Financial Result & Cash Flow: Логістика")
st.markdown("### Аналітична панель для власника бізнесу")

df = get_demo_data() # Використовуємо демо-дані для старту

# Розрахунки
df['Total Income'] = df['Прихід Готівка'] + df['Прихід Рахунок']
expense_cols = ['Оренда', 'Зарплата офіс', 'Зарплата склад', 'Зарплата водії', 'Ремонт а/м', 'ПММ', 'Офіс', 'Бухгалтерія', 'Комунальні', 'Податки']
df['Total Expenses'] = df[expense_cols].sum(axis=1)
df['Net Profit'] = df['Total Income'] - df['Total Expenses']
df['Margin %'] = (df['Net Profit'] / df['Total Income']) * 100

# --- KPI БЛОК (Вай-ефект №1) ---
m1, m2, m3, m4 = st.columns(4)
current_month = df.iloc[-1]

m1.metric("Виручка (Поточний місяць)", f"{current_month['Total Income']:,} PLN")
m2.metric("Чистий прибуток", f"{current_month['Net Profit']:,} PLN")
m3.metric("Рентабельність", f"{current_month['Margin %']:.1f}%")
m4.metric("Готівка в обороті", f"{current_month['Прихід Готівка']:,} PLN")

st.divider()

# --- ВІЗУАЛІЗАЦІЯ (Вай-ефект №2) ---
c1, c2 = st.columns([2, 1])

with c1:
    st.subheader("Динаміка Доходів та Витрат")
    fig = px.bar(df, x='Дата', y=['Total Income', 'Total Expenses'], barmode='group',
                 labels={'value': 'PLN', 'variable': 'Показник'},
                 color_discrete_map={'Total Income': '#2ECC71', 'Total Expenses': '#E74C3C'})
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("Структура витрат")
    last_expenses = current_month[expense_cols]
    fig_pie = px.pie(values=last_expenses.values, names=last_expenses.index, hole=0.4,
                     color_discrete_sequence=px.colors.sequential.RdBu)
    st.plotly_chart(fig_pie, use_container_width=True)

# --- АНАЛІЗ ПОДАТКОВОГО НАВАНТАЖЕННЯ (Вай-ефект №3) ---
st.subheader("🔍 Аналіз ефективності")
st.info(f"Середня вартість утримання автопарку (ПММ + Ремонт): **{df['ПММ'].mean() + df['Ремонт а/м'].mean():,.0f} PLN/міс**")

# Таблиця для власника
if st.checkbox("Показати детальну таблицю P&L"):
    st.dataframe(df.style.format(precision=0, thousands=" "))
