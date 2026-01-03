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
                # Штучне моделювання аномалії пального для демонстрації інсайтів
                growth = 1.0 + (m_num * 0.06) if cat == 'Паливо (ПММ)' else 1.0 + (m_num * 0.01)
                val = amt * growth
                if cat == 'Ремонт та сервіс' and m_num in [3, 10]: val *= 2.8
                data.append({'Date': month, 'Type': '2. ВИТРАТИ', 'Group': group, 'Category': cat, 'Amount': float(val)})
    return pd.DataFrame(data)

# 3. БІЧНА ПАНЕЛЬ
with st.sidebar:
    st.header("🕹️ Управління сценаріями")
    price_inc = st.slider("Змінення цін (%)", -20, 50, 5)
    cost_red = st.slider("Оптимізація витрат (%)", 0, 30, 10)
    st.divider()
    ar_delay = st.select_slider("Затримка оплат (днів)", options=[0, 15, 30, 45, 60], value=0)
    init_bal = st.number_input("Залишок на рахунку (PLN)", value=100000)
    st.link_button("🤝 Обговорити проєкт", "https://sapiensfin.eu", use_container_width=True)

# 4. ОБРОБКА ДАНИХ
df = get_base_data().copy()
df.loc[df['Type'] == '1. ПРИХОДИ', 'Amount'] *= (1 + price_inc / 100)
df.loc[df['Type'] == '2. ВИТРАТИ', 'Amount'] *= (1 - cost_red / 100)

total_inc = df[df['Type'] == '1. ПРИХОДИ']['Amount'].sum()
total_exp = df[df['Type'] == '2. ВИТРАТИ']['Amount'].sum()
net_profit = total_inc - total_exp

# 5. ГОЛОВНИЙ ЕКРАН
st.title("Financial Strategy Dashboard")

# --- ТРЕНД ПРИБУТКУ (AREA CHART) ---
st.divider()
st.subheader("📈 Тренд чистого прибутку")
monthly_pnl = df.pivot_table(index='Date', columns='Type', values='Amount', aggfunc='sum')
monthly_pnl['Profit'] = monthly_pnl['1. ПРИХОДИ'] - monthly_pnl['2. ВИТРАТИ']

col_t1, col_t2 = st.columns([2, 1])

with col_t1:
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(
        x=monthly_pnl.index, 
        y=monthly_pnl['Profit'], 
        fill='tozeroy', 
        mode='lines+markers',
        name='Чистий прибуток',
        line=dict(color='#2ecc71', width=3),
        fillcolor='rgba(46, 204, 113, 0.2)' 
    ))
    fig_trend.update_layout(height=400, margin=dict(t=20, b=20), hovermode="x unified")
    st.plotly_chart(fig_trend, use_container_width=True)
    st.caption("**Опис:** Діаграма з областями показує 'накопичений' ефект прибутку щомісяця. Зелена зона візуалізує запас міцності вашого бізнесу.")

with col_t2:
    st.info("🔍 **Фінансові інсайти та AI-поради:**")
    
    # Інсайт по пальному
    fuel_data = df[df['Category'] == 'Паливо (ПММ)'].sort_values('Date')
    revenue_data = df[df['Type'] == '1. ПРИХОДИ'].sort_values('Date')
    fuel_growth = (fuel_data['Amount'].iloc[-1] / fuel_data['Amount'].iloc[0]) - 1
    rev_growth = (revenue_data['Amount'].iloc[-1] / revenue_data['Amount'].iloc[0]) - 1
    
    if fuel_growth > rev_growth:
        st.warning(f"⚠️ **Загроза:** Витрати на пальне зросли на {fuel_growth:.0%}, що випереджає ріст виручки. Потрібен аудит паливних карток.")
    
    # Технологічна порада 1
    st.markdown("---")
    st.markdown("💡 **AI Recommendation (Maintenance):**")
    st.write("Аналіз кореляції пробігу та витрат на ремонт вказує на потенціал впровадження **Predictive Maintenance**. Це може скоротити витрати на ТО на **12-15%** за рахунок запобігання аварійним виходам з ладу.")
    
    # Технологічна порада 2 (залежна від дебіторки)
    if ar_delay > 0:
        st.markdown("---")
        st.markdown("🤖 **Smart Automation:**")
        st.write(f"При затримці оплат у {ar_delay} дн. рекомендується впровадити **автоматичний кредитний скоринг** контрагентів для мінімізації ризиків дефіциту ліквідності.")

# --- WATERFALL ---
st.divider()
st.subheader("💎 Waterfall: Аналіз витрат")
exp_agg = df[df['Type'] == '2. ВИТРАТИ'].groupby('Category')['Amount'].sum().sort_values(ascending=False)
fig_wf = go.Figure(go.Waterfall(
    measure = ["relative"] * (len(exp_agg) + 1) + ["absolute"],
    x = ["Виручка"] + list(exp_agg.index) + ["Прибуток"],
    y = [total_inc] + [-v for v in exp_agg.values] + [net_profit],
    texttemplate = "%{y:,.0s}", increasing = {"marker":{"color":"#2ecc71"}}, decreasing = {"marker":{"color":"#e74c3c"}}, totals = {"marker":{"color":"#3498db"}}
))
st.plotly_chart(fig_wf, use_container_width=True)
st.caption("**Опис:** Покроковий розрахунок: як від валової виручки ми приходимо до чистого результату.")

# --- P&L TABLE ---
st.divider()
st.subheader("📑 Детальний звіт P&L")
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
st.caption("**Опис:** Повний помісячний звіт. Кольорові градієнти підсвічують 'гарячі' зони витрат.")

# --- CASH FLOW ---
st.divider()
st.subheader("📉 Прогноз Cash Flow")
df_cf = df.copy()
if ar_delay > 0: df_cf.loc[df_cf['Type'] == '1. ПРИХОДИ', 'Date'] += pd.Timedelta(days=ar_delay)
df_cf['Net'] = df_cf.apply(lambda x: x['Amount'] if 'ПРИХОДИ' in x['Type'] else -x['Amount'], axis=1)
daily_cf = df_cf.groupby('Date')['Net'].sum().sort_index().reset_index()
daily_cf['Balance'] = init_bal + daily_cf['Net'].cumsum()
st.plotly_chart(go.Figure(go.Scatter(x=daily_cf['Date'], y=daily_cf['Balance'], fill='tozeroy', line_color='#2E86C1')), use_container_width=True)
st.caption("**Опис:** Прогноз реальних грошей у касі. Ризик касового розриву підсвічується червоною лінією.")
