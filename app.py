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
    
    # Розподіл на постійні та змінні витрати для Точки беззбитковості
    expenses = {
        'Fixed': {'Оренда та склад': 40000, 'Зарплата офіс': 55000, 'Амортизація': 10000},
        'Variable': {'Зарплата водії': 180000, 'Паливо (ПММ)': 95000, 'Лізинг авто': 70000, 'Ремонт та сервіс': 20000, 'Маркетинг': 15000},
        'Taxes': {'Податки та збори': 45000}
    }

    for month in months:
        m_num = month.month
        rev_f = 0.7 if m_num in [3, 10] else 1.0 
        
        # Дохід
        data.append({'Date': month, 'Type': '1. ПРИХОДИ', 'Group': 'Revenue', 'Category': 'Виручка B2B', 'Amount': 580000.0 * rev_f})
        
        # Витрати
        for group, cats in expenses.items():
            for cat, amt in cats.items():
                val = amt * (1.0 + m_num * 0.01) # невелика динаміка
                if cat == 'Ремонт та сервіс' and m_num in [3, 10]: val *= 2.8
                data.append({'Date': month, 'Type': '2. ВИТРАТИ', 'Group': group, 'Category': cat, 'Amount': float(val)})
            
    return pd.DataFrame(data)

# 3. БІЧНА ПАНЕЛЬ
with st.sidebar:
    st.header("🕹️ Управління сценаріями")
    price_inc = st.slider("Змінення цін (%)", -20, 50, 5)
    cost_red = st.slider("Оптимізація витрат (%)", 0, 30, 10)
    
    st.divider()
    st.subheader("💳 Дебіторська заборгованість")
    ar_delay = st.select_slider("Затримка оплат від клієнтів (днів)", options=[0, 15, 30, 45, 60], value=0)
    
    st.divider()
    init_bal = st.number_input("Залишок на рахунку (PLN)", value=100000)
    st.link_button("🤝 Обговорити проєкт", "https://sapiensfin.eu", use_container_width=True)

# 4. ОБРОБКА ДАНИХ
df = get_base_data().copy()
df.loc[df['Type'] == '1. ПРИХОДИ', 'Amount'] *= (1 + price_inc / 100)
df.loc[df['Type'] == '2. ВИТРАТИ', 'Amount'] *= (1 - cost_red / 100)

# Розрахунок точки беззбитковості (BEP)
fixed_costs = df[df['Group'] == 'Fixed']['Amount'].sum() / 12
var_costs_ratio = df[df['Group'] == 'Variable']['Amount'].sum() / df[df['Type'] == '1. ПРИХОДИ']['Amount'].sum()
bep_monthly = fixed_costs / (1 - var_costs_ratio) if var_costs_ratio < 1 else 0

# 5. МЕТРИКИ
st.title("Financial Strategy Dashboard")
total_inc = df[df['Type'] == '1. ПРИХОДИ']['Amount'].sum()
total_exp = df[df['Type'] == '2. ВИТРАТИ']['Amount'].sum()
net_profit = total_inc - total_exp

m1, m2, m3, m4 = st.columns(4)
m1.metric("Річна Виручка", f"{total_inc:,.0f}")
m2.metric("Чистий Прибуток", f"{net_profit:,.0f}")
m3.metric("Точка беззбитк. (міс.)", f"{bep_monthly:,.0f}")
m4.metric("Рентабельність", f"{(net_profit/total_inc*100):.1f}%")

# 6. WATERFALL
st.divider()
st.subheader("💎 Waterfall: Від Виручки до Податків та Прибутку")
exp_agg = df[df['Type'] == '2. ВИТРАТИ'].groupby(['Group', 'Category'])['Amount'].sum().reset_index().sort_values('Amount', ascending=False)

fig_wf = go.Figure(go.Waterfall(
    measure = ["relative"] * (len(exp_agg) + 1) + ["absolute"],
    x = ["Виручка"] + list(exp_agg['Category']) + ["Чистий прибуток"],
    y = [total_inc] + [-v for v in exp_agg['Amount']] + [net_profit],
    textposition = "outside",
    texttemplate = "%{y:,.0s}",
    increasing = {"marker":{"color":"#2ecc71"}},
    decreasing = {"marker":{"color":"#e74c3c"}},
    totals = {"marker":{"color":"#3498db"}}
))
st.plotly_chart(fig_wf, use_container_width=True)

# 7. ТАБЛИЦЯ P&L (З ВИДІЛЕННЯМ ПОДАТКІВ)
st.divider()
st.subheader("📑 Звіт P&L з податковим блоком")

df['Month'] = df['Date'].dt.strftime('%m-%Y')
# Додаємо групу в індекс для виділення податків
pnl = df.pivot_table(index=['Type', 'Group', 'Category'], columns='Month', values='Amount', aggfunc='sum')
sorted_months = sorted(df['Month'].unique(), key=lambda x: pd.to_datetime(x, format='%m-%Y'))
pnl = pnl[sorted_months]

st.dataframe(
    pnl.style.format("{:,.0f}")
    .background_gradient(cmap='GnBu', subset=pd.IndexSlice[('1. ПРИХОДИ', slice(None), slice(None)), :])
    .background_gradient(cmap='YlOrRd', subset=pd.IndexSlice[('2. ВИТРАТИ', ['Fixed', 'Variable'], slice(None)), :])
    .apply(lambda x: ['background-color: #fce4ec; font-weight: bold' if x.name[1] == 'Taxes' else '' for _ in x], axis=1),
    use_container_width=True
)

# Експорт у CSV
csv = pnl.to_csv().encode('utf-8')
st.download_button("📥 Завантажити P&L в Excel (CSV)", data=csv, file_name='financial_report.csv', mime='text/csv')

# 8. CASH FLOW ТА ДЕБІТОРКА
st.divider()
st.subheader("📉 Cash Flow: Вплив затримки оплат")

# Моделювання дебіторки: зміщуємо вхідний потік на N днів
df_cf = df.copy()
if ar_delay > 0:
    df_cf.loc[df_cf['Type'] == '1. ПРИХОДИ', 'Date'] += pd.Timedelta(days=ar_delay)

df_cf['Net'] = df_cf.apply(lambda x: x['Amount'] if 'ПРИХОДИ' in x['Type'] else -x['Amount'], axis=1)
daily_cf = df_cf.groupby('Date')['Net'].sum().sort_index().reset_index()
daily_cf['Balance'] = init_bal + daily_cf['Net'].cumsum()

fig_cf = go.Figure()
fig_cf.add_trace(go.Scatter(x=daily_cf['Date'], y=daily_cf['Balance'], fill='tozeroy', line_color='#2E86C1'))
fig_cf.add_hline(y=0, line_dash="dash", line_color="red")
st.plotly_chart(fig_cf, use_container_width=True)

if daily_cf['Balance'].min() < 0:
    st.error(f"🚨 ОБЕРЕЖНО! Затримка в {ar_delay} дн. призведе до розриву в {abs(daily_cf['Balance'].min()):,.0f} PLN")
