import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

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
base_df = get_base_data().copy()
# Сценарій "ПІСЛЯ"
opt_df = base_df.copy()
opt_df.loc[opt_df['Type'] == '1. ПРИХОДИ', 'Amount'] *= (1 + price_inc / 100)
opt_df.loc[opt_df['Type'] == '2. ВИТРАТИ', 'Amount'] *= (1 - cost_red / 100)

total_inc = opt_df[opt_df['Type'] == '1. ПРИХОДИ']['Amount'].sum()
total_exp = opt_df[opt_df['Type'] == '2. ВИТРАТИ']['Amount'].sum()
net_profit = total_inc - total_exp

# 5. ГОЛОВНИЙ ЕКРАН
st.title("Financial Strategy Dashboard")

# --- ПОРІВНЯННЯ СТРУКТУРИ (КРУГОВІ ДІАГРАМИ) ---
st.divider()
st.subheader("📊 Порівняння структури капіталу (Рік)")
col_p1, col_p2 = st.columns(2)

def prepare_pie_data(temp_df):
    inc = temp_df[temp_df['Type'] == '1. ПРИХОДИ']['Amount'].sum()
    exp = temp_df[temp_df['Type'] == '2. ВИТРАТИ']['Amount'].sum()
    prof = max(0, inc - exp)
    return pd.DataFrame({'Назва': ['Витрати', 'Чистий прибуток'], 'Сума': [exp, prof]})

with col_p1:
    st.markdown("<center><b>БАЗОВИЙ ПЛАН (ДО)</b></center>", unsafe_allow_html=True)
    fig_pie_before = px.pie(prepare_pie_data(base_df), values='Сума', names='Назва', 
                            color_discrete_sequence=['#e74c3c', '#27ae60'], hole=0.4)
    fig_pie_before.update_layout(height=300, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig_pie_before, use_container_width=True)

with col_p2:
    st.markdown("<center><b>ОПТИМІЗОВАНИЙ ПЛАН (ПІСЛЯ)</b></center>", unsafe_allow_html=True)
    fig_pie_after = px.pie(prepare_pie_data(opt_df), values='Сума', names='Назва', 
                           color_discrete_sequence=['#e74c3c', '#2ecc71'], hole=0.4)
    fig_pie_after.update_layout(height=300, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig_pie_after, use_container_width=True)

# --- ТРЕНД ПРИБУТКУ ---
st.divider()
st.subheader("📈 Тренд чистого прибутку")
monthly_pnl = opt_df.pivot_table(index='Date', columns='Type', values='Amount', aggfunc='sum')
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
    st.caption("**Опис:** Діаграма показує стабільність вашого прибутку. Зелена зона — це ваш 'запас міцності'.")

with col_t2:
    st.info("🔍 **Фінансові інсайти та AI-поради:**")
    
    # Спрощений текст про ТО
    st.markdown("💡 **Розумне обслуговування (AI):**")
    st.write(
        "Наша модель прогнозує поломки до того, як вони стануть критичними. "
        "Це дозволяє замінювати запчастини вчасно, що **знижує витрати на ремонт на 12-15%** "
        "та рятує від дорогих простоїв вантажівок."
    )
    
    # Інсайт по пальному
    fuel_data = opt_df[opt_df['Category'] == 'Паливо (ПММ)'].sort_values('Date')
    fuel_growth = (fuel_data['Amount'].iloc[-1] / fuel_data['Amount'].iloc[0]) - 1
    if fuel_growth > 0.1:
        st.warning(f"⚠️ **Паливо:** Витрати на ПММ зростають занадто швидко (+{fuel_growth:.0%}). Варто перевірити ефективність маршрутів.")

# --- WATERFALL ---
st.divider()
st.subheader("💎 Waterfall: Від виручки до прибутку")
exp_agg = opt_df[opt_df['Type'] == '2. ВИТРАТИ'].groupby('Category')['Amount'].sum().sort_values(ascending=False)
fig_wf = go.Figure(go.Waterfall(
    measure = ["relative"] * (len(exp_agg) + 1) + ["absolute"],
    x = ["Виручка"] + list(exp_agg.index) + ["Прибуток"],
    y = [total_inc] + [-v for v in exp_agg.values] + [net_profit],
    texttemplate = "%{y:,.0s}", increasing = {"marker":{"color":"#2ecc71"}}, decreasing = {"marker":{"color":"#e74c3c"}}, totals = {"marker":{"color":"#3498db"}}
))
st.plotly_chart(fig_wf, use_container_width=True)

# --- P&L TABLE ---
st.divider()
st.subheader("📑 Детальний звіт P&L")
opt_df['Month'] = opt_df['Date'].dt.strftime('%m-%Y')
sorted_months = sorted(opt_df['Month'].unique(), key=lambda x: pd.to_datetime(x, format='%m-%Y'))
pnl = opt_df.pivot_table(index=['Type', 'Group', 'Category'], columns='Month', values='Amount', aggfunc='sum')[sorted_months]
profit_row = pnl.loc['1. ПРИХОДИ'].sum() - pnl.loc['2. ВИТРАТИ'].sum()
profit_df = pd.DataFrame([profit_row], index=pd.MultiIndex.from_tuples([('0. РЕЗУЛЬТАТ', 'Total', 'ЧИСТИЙ ПРИБУТОК')], names=['Type', 'Group', 'Category']), columns=pnl.columns)
pnl_final = pd.concat([profit_df, pnl]).sort_index()

def apply_pnl_styles(styler):
    styler.apply(lambda x: ['background-color: #3498db; color: white; font-weight: bold' if x.name[0] == '0. РЕЗУЛЬТАТ' else '' for _ in x], axis=1)
    styler.background_gradient(cmap='GnBu', subset=pd.IndexSlice[('1. ПРИХОДИ', slice(None), slice(None)), :])
    styler.background_gradient(cmap='YlOrRd', subset=pd.IndexSlice[('2. ВИТРАТИ', ['Fixed', 'Variable'], slice(None)), :])
    return styler

st.dataframe(apply_pnl_styles(pnl_final.style.format("{:,.0f}")), use_container_width=True)

# --- CASH FLOW ---
st.divider()
st.subheader("📉 Прогноз залишків на рахунку (Cash Flow)")
df_cf = opt_df.copy()
if ar_delay > 0: df_cf.loc[df_cf['Type'] == '1. ПРИХОДИ', 'Date'] += pd.Timedelta(days=ar_delay)
df_cf['Net'] = df_cf.apply(lambda x: x['Amount'] if 'ПРИХОДИ' in x['Type'] else -x['Amount'], axis=1)
daily_cf = df_cf.groupby('Date')['Net'].sum().sort_index().reset_index()
daily_cf['Balance'] = init_bal + daily_cf['Net'].cumsum()
st.plotly_chart(go.Figure(go.Scatter(x=daily_cf['Date'], y=daily_cf['Balance'], fill='tozeroy', line_color='#2E86C1')), use_container_width=True)
