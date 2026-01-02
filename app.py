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
        # Сезонність доходів
        rev_f = 0.6 if m_num in [3, 10] else 1.0
        # Динамічне зростання витрат до кінця року (щоб кругові діаграми відрізнялися)
        dynamic_f = 1.0 + (m_num * 0.03) 
        
        # Дохід
        data.append({'Date': month, 'Type': '1. ПРИХОДИ', 'Category': 'Виручка B2B', 'Amount': 600000.0 * rev_f})
        
        # Витрати
        for cat, amt in expense_categories.items():
            val = amt
            if cat == 'Ремонт та сервіс' and m_num in [3, 10]:
                val *= 3.5
            elif cat in ['Паливо (ПММ)', 'Зарплата водії']:
                val *= dynamic_f # ці категорії ростуть до кінця року
            
            data.append({'Date': month, 'Type': '2. ВИТРАТИ', 'Category': cat, 'Amount': float(val)})
            
    return pd.DataFrame(data)

# 3. БІЧНА ПАНЕЛЬ
with st.sidebar:
    st.header("🕹️ Симулятор рішень")
    price_inc = st.slider("Збільшення цін (%)", 0, 50, 0)
    cost_red = st.slider("Оптимізація витрат (%)", 0, 50, 0)
    st.write("---")
    st.info("Ця модель демонструє вплив ваших рішень на фінансовий результат у реальному часі.")

# 4. ОБРОБКА ДАНИХ
df_base = get_base_data()
df = df_base.copy()

# Застосування слайдерів
df.loc[df['Type'] == '1. ПРИХОДИ', 'Amount'] *= (1 + price_inc / 100)
df.loc[df['Type'] == '2. ВИТРАТИ', 'Amount'] *= (1 - cost_red / 100)
df['Month_Year'] = df['Date'].dt.strftime('%m-%Y')

# Розрахунок метрик
total_inc = df[df['Type'] == '1. ПРИХОДИ']['Amount'].sum()
total_exp = df[df['Type'] == '2. ВИТРАТИ']['Amount'].sum()
net_profit = total_inc - total_exp
ros = (net_profit / total_inc * 100) if total_inc > 0 else 0

# 5. ГОЛОВНИЙ ЕКРАН
st.title("Financial Strategy Dashboard")

c1, c2, c3 = st.columns(3)
c1.metric("Річний оборот", f"{total_inc:,.0f} PLN")
c2.metric("Чистий прибуток", f"{net_profit:,.0f} PLN")
c3.metric("Рентабельність (ROS)", f"{ros:.1f}%")

# 6. WATERFALL CHART (З ЧИСЛОВИМИ МІТКАМИ)
st.divider()
st.subheader("💎 Математика прибутку: Waterfall")
exp_summary = df[df['Type'] == '2. ВИТРАТИ'].groupby('Category')['Amount'].sum().sort_values(ascending=False)

fig_wf = go.Figure(go.Waterfall(
    measure = ["relative"] * (len(exp_summary) + 1) + ["total"],
    x = ["Виручка"] + list(exp_summary.index) + ["Чистий прибуток"],
    y = [total_inc] + [-v for v in exp_summary.values] + [0],
    texttemplate = "%{y:,.0f}", # Відображення значень над стовпчиками
    textposition = "outside",
    connector = {"line":{"color":"rgba(63, 63, 63, 0.5)"}},
    increasing = {"marker":{"color":"#2ecc71"}},
    decreasing = {"marker":{"color":"#e74c3c"}},
    totals = {"marker":{"color":"#3498db"}}
))
fig_wf.update_layout(height=500, margin=dict(t=50))
st.plotly_chart(fig_wf, use_container_width=True)

# 7. КРУГОВІ ДІАГРАМИ (ПОРІВНЯННЯ СТРУКТУРИ)
st.divider()
st.subheader("📊 Структура витрат: Січень vs Грудень")
cp1, cp2 = st.columns(2)
for i, col in enumerate([cp1, cp2]):
    m_num = 1 if i == 0 else 12
    p_data = df[(df['Type'] == '2. ВИТРАТИ') & (df['Date'].dt.month == m_num)]
    fig = go.Figure(data=[go.Pie(labels=p_data['Category'], values=p_data['Amount'], hole=.4)])
    fig.update_layout(title="Структура у Січні" if i == 0 else "Структура у Грудні", height=400)
    col.plotly_chart(fig, use_container_width=True)

# 8. ТАБЛИЦЯ P&L З РЯДКОМ ПРИБУТКУ
st.divider()
st.subheader("📑 Детальний звіт P&L за місяцями")

# Створення основної таблиці
pnl = df.pivot_table(index=['Type', 'Category'], columns='Month_Year', values='Amount', aggfunc='sum')
cols_sorted = sorted(df['Month_Year'].unique(), key=lambda x: pd.to_datetime(x, format='%m-%Y'))
pnl = pnl[cols_sorted]

# Розрахунок рядка прибутку
profit_row = pnl.loc['1. ПРИХОДИ'].sum() - pnl.loc['2. ВИТРАТИ'].sum()
profit_df = pd.DataFrame([profit_row], index=pd.MultiIndex.from_tuples([('3. РЕЗУЛЬТАТ', 'ЧИСТИЙ ПРИБУТОК')], names=['Type', 'Category']))

# Додавання прибутку в таблицю
pnl_final = pd.concat([pnl, profit_df])

st.dataframe(
    pnl_final.style.format("{:,.0f}")
    .background_gradient(cmap='GnBu', subset=pd.IndexSlice[('1. ПРИХОДИ', slice(None)), :])
    .background_gradient(cmap='YlOrRd', subset=pd.IndexSlice[('2. ВИТРАТИ', slice(None)), :])
    .highlight_max(axis=1, color='#d1f2eb', subset=pd.IndexSlice[('3. РЕЗУЛЬТАТ', slice(None)), :]),
    use_container_width=True
)

# 9. ОБГОВОРИТИ ПРОЄКТ
st.divider()
col_f1, col_f2, col_f3 = st.columns([1, 2, 1])
with col_f2:
    st.markdown("<h3 style='text-align: center;'>Сподобалась модель?</h3>", unsafe_allow_html=True)
    st.link_button("🤝 Обговорити ваш проєкт", "https://sapiensfin.eu", use_container_width=True)
    st.markdown("<p style='text-align: center; color: gray;'>Налаштуємо професійний фінлік для вашого бізнесу</p>", unsafe_allow_html=True)

# 10. CASH FLOW (Довідково внизу)
with st.expander("Подивитися прогноз Cash Flow"):
    df['Change'] = df.apply(lambda x: x['Amount'] if 'ПРИХОДИ' in x['Type'] else -x['Amount'], axis=1)
    cf_data = df.groupby('Date')['Change'].sum().reset_index()
    cf_data['Balance'] = 50000 + cf_data['Change'].cumsum()
    st.line_chart(cf_data.set_index('Date')['Balance'])
