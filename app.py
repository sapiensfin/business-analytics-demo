import streamlit as st
import pandas as pd
import plotly.express as px

# Налаштування сторінки
st.set_page_config(page_title="Business Architect Dashboard", layout="wide")

st.title("📊 Аналітична панель для бізнесу в Польщі")
st.sidebar.header("Налаштування")

# 1. Завантаження файлу
uploaded_file = st.sidebar.file_uploader("Завантажте ваш звіт (Excel/CSV)", type=['csv', 'xlsx'])

if uploaded_file is not None:
    # Читання даних
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
    
    # 2. Показ основних метрик (KPI)
    col1, col2, col3 = st.columns(3)
    total_rev = df['Сума'].sum()
    total_profit = df['Прибуток'].sum()
    margin = (total_profit / total_rev) * 100
    
    col1.metric("Виручка (PLN)", f"{total_rev:,.2f}")
    col2.metric("Чистий прибуток", f"{total_profit:,.2f}")
    col3.metric("Маржинальність", f"{margin:.1f}%")

    # 3. Візуалізація
    st.subheader("📈 Динаміка продажів")
    fig = px.line(df, x='Дата', y='Сума', title="Продажі по днях")
    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Будь ласка, завантажте файл у бічну панель, щоб почати аналіз.")
    st.warning("Приклад структури файлу: Дата | Категорія | Сума | Прибуток")