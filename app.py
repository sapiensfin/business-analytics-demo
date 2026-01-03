import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. НАЛАШТУВАННЯ СТОРІНКИ
st.set_page_config(page_title="SapiensFin | Professional Demo", layout="wide")

# 2. ГЕНЕРАЦІЯ ДАНИХ
@st.cache_data
def get_base_data():
    data = []
    months = pd.date_range(start="2025-01-01", periods=12, freq='MS')
    expenses = {
        'Fixed': {'Оренда та склад': 40000, 'Зарплата офіс': 55000, 'Амортизація': 10000},
        'Variable': {'Зарплата водії': 180000, 'Паливо (ПММ)': 95000, 'Лізинг авто': 70000, 'Ремонт та сервіс': 20000, 'Маркетинг': 15000},
        'Taxes': {'Податки та збори': 45000}
    }
    for month in months:
        m_num = month.month
        rev_f = 0.7 if m_num in [3, 10] else 1.0 
        data.append({'Date': month, 'Type': '1. ПРИХОДИ', 'Group': 'Revenue', 'Category': 'Виручка B2B', 'Amount': 580000.0 * rev_f})
        for group, cats in expenses.items():
            for cat, amt in cats.items():
                # Моделювання зростання витрат (особливо палива) для наочності
                growth = 1.0 + (m_num * 0.06) if cat == 'Паливо (ПММ)' else 1.0 + (m_num * 0.01)
                val = amt * growth
                if cat == 'Ремонт та сервіс' and m_num in [3, 10]: val *= 2.8
                data.append({'Date': month, 'Type': '2. ВИТРАТИ', 'Group': group, 'Category': cat, 'Amount': float(val)})
    return pd.DataFrame(data)

# 3. БІЧНА ПАНЕЛЬ (КЕРУВАННЯ)
with st.sidebar:
    st.header("🕹️ Управління сценаріями")
    price_inc = st.slider("Змінення цін (%)", -20, 50, 5)
    cost_red = st.slider("Оптимізація витрат (%)", 0, 30, 10)
    st.divider()
    ar_delay = st.select_slider("Затримка оплат (днів)", options=[0, 15, 30, 45, 60], value=0)
    init_bal = st.number_input("Залишок на рахунку (PLN)", value=100000)
    st.link_button("🤝 Обговорити проєкт", "https://sapiensfin.eu", use_container_width=True)

# 4. ОБРОБКА ДАНИХ ЗА СЦЕНАРІЄМ
df = get_base_data().copy()
df.loc[df['Type'] == '1. ПРИХОДИ', 'Amount'] *= (1 + price_inc / 100)
df.loc[df['Type'] == '2. ВИТРАТИ', 'Amount'] *= (1 - cost_red / 100)

total_inc = df[df['Type'] == '1. ПРИХОДИ']['Amount'].sum()
total_exp = df[df['Type'] == '2. ВИТРАТИ']['Amount'].sum()
net_profit = total_inc - total_exp

# 5. ВІЗУАЛІЗАЦІЯ
st.title("Financial Strategy Dashboard")

# --- БЛОК 1: ТРЕНД ПРИБУТКУ ТА ІНСАЙТИ ---
st.divider()
st.subheader("📈 Тренд чистого прибутку")
monthly_pnl = df.pivot_table(index='Date', columns='Type', values='Amount', aggfunc='sum')
monthly_pnl['Profit'] = monthly_pnl['1. ПРИХОДИ'] - monthly_pnl['2. ВИТРАТИ']

col_t1, col_t2 = st.columns([2, 1])
with col_t1:
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(
        x=monthly_pnl.index, y=monthly_pnl['Profit'], fill='tozeroy', 
        mode='lines+markers', name='Прибуток', line=dict(color='#2ecc71', width=3),
        fillcolor='rgba(46, 204, 113, 0.2)' 
    ))
    fig_trend.update_layout(height=350, margin=dict(t=20, b=20), hovermode="x unified")
    st.plotly_chart(fig_trend, use_container_width=True)
    st.caption("**Опис:** Діаграма відображає помісячну динаміку чистого прибутку. Зелена зона візуалізує запас міцності бізнесу.")

with col_t2:
    st.info("🔍 **Фінансові інсайти:**")
    fuel_data = df[df['Category'] == 'Паливо (ПММ)'].sort_values('Date')
    revenue_data = df[df['Type'] == '1. ПРИХОДИ'].sort_values('Date')
    fuel_growth = (fuel_data['Amount'].iloc[-1] / fuel_data['Amount'].iloc[0]) - 1
    rev_growth = (revenue_data['Amount'].iloc[-1] / revenue_data['Amount'].iloc[0]) - 1
    
    if fuel_growth > rev_growth:
        st.warning(f"⚠️ **Загрозлива тенденція:** Витрати на пальне зросли на {fuel_growth:.0%}, що випереджає ріст виручки ({rev_growth:.0%}). Це не пояснюється об'ємом перевезень.")
    
    st.divider()
    st.markdown("💡 **Розумна дебіторка (AI):**")
    st.write("Система ідентифікувала групу 'критичних боржників'. Впровадження алгоритму автоматичного скорингу дозволить посилити контроль над оплатністю та знизити ризик касового розриву.")

# --- БЛОК 2: WATERFALL (МАТЕМАТИКА ВИРУЧКИ) ---
st.divider()
st.subheader("💎 Waterfall: Математика формування прибутку")
exp_agg = df[df['Type'] == '2. ВИТРАТИ'].groupby('Category')['Amount'].sum().sort_values(ascending=False)

fig_wf = go.Figure(go.Waterfall(
    measure = ["absolute"] + (["relative"] * len(exp_agg)) + ["total"],
    x = ["Виручка"] + list(exp_agg.index) + ["Чистий прибуток"],
    y = [total_inc] + [-v for v in exp_agg.values] + [0], 
    texttemplate = "%{y:,.0s}",
    increasing = {"marker":{"color":"#2ecc71"}},
    decreasing = {"marker":{"color":"#e74c3c"}},
    totals = {"marker":{"color":"#3498db"}}
))
fig_wf.update_layout(height=500)
st.plotly_chart(fig_wf, use_container_width=True)
st.caption("**Опис:** Візуальний баланс: як кожна гривня витрат 'з'їдає' вхідну виручку до фінального прибутку.")

# --- БЛОК 3: КРУГОВІ ДІАГРАМИ (СТРУКТУРА) ---
st.divider()
st.subheader("📊 Структура витрат: Порівняння Січень vs Грудень")
c_p1, c_p2 = st.columns(2)
for i, col in enumerate([c_p1, c_p2]):
    m_target = 1 if i == 0 else 12
    pie_data = df[(df['Type'] == '2. ВИТРАТИ') & (df['Date'].dt.month == m_target)]
    fig = go.Figure(data=[go.Pie(labels=pie_data['Category'], values=pie_data['Amount'], hole=.4)])
    fig.update_layout(title="Січень (Статті витрат)" if i == 0 else "Грудень (Прогноз)", height=350)
    col.plotly_chart(fig, use_container_width=True)
st.caption("**Опис:** Порівняння структури витрат. Допомагає побачити, які статті починають домінувати в бюджеті до кінця року.")

# --- БЛОК 4: КРИТИЧНІ БОРЖНИКИ ---
st.divider()
st.subheader("🚩 Критичні боржники (Дебіторська заборгованість)")
debt_data = {
    'Контрагент': ['Sp.z o.o. Logistics One', 'Uslugi Transportowe Kowalski', 'STR Warszawa', 'JDG Piotr Sokolowski'],
    'Сума боргу (PLN)': [145000, 89000, 62000, 15000],
    'Прострочення (днів)': [45, 32, 18, 5],
    'Статус ризику': ['🔴 Високий', '🟠 Середній', '🟡 Низький', '🟢 Мінімальний']
}
st.table(pd.DataFrame(debt_data))
st.caption("**Опис:** Список клієнтів з найбільшим ризиком неплатежів. Потребує уваги відділу контролінгу.")

# --- БЛОК 5: P&L ТАБЛИЦЯ ---
st.divider()
st.subheader("📑 Помісячний звіт P&L")
df['Month'] = df['Date'].dt.strftime('%m-%Y')
sorted_months = sorted(df['Month'].unique(), key=lambda x: pd.to_datetime(x, format='%m-%Y'))
pnl = df.pivot_table(index=['Type', 'Group', 'Category'], columns='Month', values='Amount', aggfunc='sum')[sorted_months]
profit_row = pnl.loc['1. ПРИХОДИ'].sum() - pnl.loc['2. ВИТРАТИ'].sum()
profit_df = pd.DataFrame([profit_row], index=pd.MultiIndex.from_tuples([('0. РЕЗУЛЬТАТ', 'Total', 'ЧИСТИЙ ПРИБУТОК')], names=['Type', 'Group', 'Category']), columns=pnl.columns)
pnl_final = pd.concat([profit_df, pnl]).sort_index()

def apply_pnl_styles(styler):
    styler.apply(lambda x: ['background-color: #3498db; color: white; font-weight: bold' if x.name[0] == '0. РЕЗУЛЬТАТ' else '' for _ in x], axis=1)
    styler.apply(lambda x: ['background-color: #b71c1c; color: white; font-weight: bold' if x.name[1] == 'Taxes' else '' for _ in x], axis=1)
    styler.background_gradient(cmap='GnBu', subset=pd.IndexSlice[('1. ПРИХОДИ', slice(None), slice(None)), :])
    styler.background_gradient(cmap='YlOrRd', subset=pd.IndexSlice[('2. ВИТРАТИ', ['Fixed', 'Variable'], slice(None)), :])
    return styler

st.dataframe(apply_pnl_styles(pnl_final.style.format("{:,.0f}")), use_container_width=True)
st.caption("**Опис:** Деталізована таблиця доходів та витрат. Кольорові градієнти допомагають швидко знайти аномалії.")

# --- БЛОК 6: CASH FLOW ---
st.divider()
st.subheader("📉 Прогноз Cash Flow")
df_cf = df.copy()
if ar_delay > 0: df_cf.loc[df_cf['Type'] == '1. ПРИХОДИ', 'Date'] += pd.Timedelta(days=ar_delay)
df_cf['Net'] = df_cf.apply(lambda x: x['Amount'] if 'ПРИХОДИ' in x['Type'] else -x['Amount'], axis=1)
daily_cf = df_cf.groupby('Date')['Net'].sum().sort_index().reset_index()
daily_cf['Balance'] = init_bal + daily_cf['Net'].cumsum()

st.plotly_chart(go.Figure(go.Scatter(x=daily_cf['Date'], y=daily_cf['Balance'], fill='tozeroy', line_color='#2E86C1')), use_container_width=True)
st.caption("**Опис:** Прогноз наявності грошей на рахунку. Дозволяє передбачити моменти касових розривів.")

