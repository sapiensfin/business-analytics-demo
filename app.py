import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Налаштування
st.set_page_config(page_title="SapiensFin | Demo", layout="wide")

# 2. Дані
def get_clean_data():
    data = []
    months = pd.date_range(start="2025-01-01", periods=12, freq='MS')
    categories = {
        'Оренда': 55000, 'Зарплати': 245000, 'Паливо': 95000, 
        'Лізинг': 75000, 'Ремонт': 25000, 'Маркетинг': 20000
    }
    for m in months:
        # Виручка
        rev = 600000.0 if m.month not in [3, 10] else 360000.0
        data.append({'Дата': m, 'Тип': '1. ДОХОДИ', 'Стаття': 'Виручка', 'Сума': rev})
        # Витрати
        for cat, amt in categories.items():
            val = amt * 3.5 if (cat == 'Ремонт' and m.month in [3, 10]) else amt
            data.append({'Дата': m, 'Тип': '2. ВИТРАТИ', 'Стаття': cat, 'Сума': float(val)})
    return pd.DataFrame(data)

# 3. Sidebar
with st.sidebar:
    st.header("🕹️ Налаштування")
    p_inc = st.slider("Ріст цін (%)", 0, 50, 0)
    c_red = st.slider("Оптимізація витрат (%)", 0, 50, 0)
    st.markdown("---")
    st.markdown("Developed by [Sapiens Fin](https://sapiensfin.eu)")

# 4. Логіка
df = get_clean_data()
df.loc[df['Тип'] == '1. ДОХОДИ', 'Сума'] *= (1 + p_inc / 100)
df.loc[df['Тип'] == '2. ВИТРАТИ', 'Сума'] *= (1 - c_red / 100)
df['Місяць'] = df['Дата'].dt.strftime('%m-%Y')

# 5. Метрики
st.title("Financial Strategy Dashboard")
inc = df[df['Тип'] == '1. ДОХОДИ']['Сума'].sum()
exp = df[df['Тип'] == '2. ВИТРАТИ']['Сума'].sum()
prof = inc - exp

col1, col2, col3 = st.columns(3)
col1.metric("Оборот", f"{inc:,.0f} PLN")
col2.metric("Прибуток", f"{prof:,.0f} PLN")
col3.metric("ROS", f"{(prof/inc*100):.1f}%")

# 6. Кругові діаграми
st.subheader("📊 Структура витрат (Початок vs Кінець року)")
c_pie1, c_pie2 = st.columns(2)
for i, col in enumerate([c_pie1, c_pie2]):
    m_idx = 1 if i == 0 else 12
    d = df[(df['Тип'] == '2. ВИТРАТИ') & (df['Дата'].dt.month == m_idx)]
    fig = go.Figure(data=[go.Pie(labels=d['Стаття'], values=d['Сума'], hole=.4)])
    fig.update_layout(title="Січень" if i == 0 else "Грудень", height=350)
    col.plotly_chart(fig, use_container_width=True)

# 7. Таблиця P&L - ТУТ БУЛА ПОМИЛКА
st.subheader("📑 Детальний звіт P&L")
# Зверніть увагу: values='Сума' тепер точно відповідає назві в датафреймі
pnl = df.pivot_table(index=['Тип', 'Стаття'], columns='Місяць', values='Сума', aggfunc='sum')
# Сортуємо колонки правильно
m_order = sorted(df['Місяць'].unique(), key=lambda x: pd.to_datetime(x, format='%m-%Y'))
pnl = pnl[m_order]

st.dataframe(pnl.style.format("{:,.0f}").background_gradient(cmap='RdYlGn', axis=1), use_container_width=True)

# 8. Cash Flow
st.subheader("📉 Прогноз Cash Flow")
df['Flow'] = df.apply(lambda x: x['Сума'] if 'ДОХОДИ' in x['Тип'] else -x['Сума'], axis=1)
cf = df.groupby('Дата')['Flow'].sum().cumsum()
st.line_chart(cf)
