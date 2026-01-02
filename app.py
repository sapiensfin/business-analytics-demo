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
        
        # Дохід
        data.append({'Date': month, 'Type': '1. ПРИХОДИ', 'Group': 'Revenue', 'Category': 'Виручка B2B', 'Amount': 580000.0 * rev_f})
        
        # Витрати
        for group, cats in expenses.items():
            for cat, amt in cats.items():
                val = amt * (1.0 + m_num * 0.015)
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

# 5. МЕТРИКИ
st.title("Financial Strategy Dashboard")
total_inc = df[df['Type'] == '1. ПРИХОДИ']['Amount'].sum()
total_exp = df[df['Type'] == '2. ВИТРАТИ']['Amount'].sum()
net_profit = total_inc - total_exp

m1, m2, m3, m4 = st.columns(4)
m1.metric("Річна Виручка", f"{total_inc:,.0f}")
m2.metric("Чистий Прибуток", f"{net_profit:,.0f}")
m3.metric("Рентабельність (ROS)", f"{(net_profit/total_inc*100):.1f}%")
m4.metric("Статус", "✅ Прибутковий" if net_profit > 0 else "❌ Збитковий")

# 6. WATERFALL
st.divider()
st.subheader("💎 Waterfall: Математика формування прибутку")
exp_agg = df[df['Type'] == '2. ВИТРАТИ'].groupby('Category')['Amount'].sum().sort_values(ascending=False)

fig_wf = go.Figure(go.Waterfall(
    measure = ["relative"] * (len(exp_agg) + 1) + ["absolute"],
    x = ["Виручка"] + list(exp_agg.index) + ["Чистий прибуток"],
    y = [total_inc] + [-v for v in exp_agg.values] + [net_profit],
    textposition = "outside",
    texttemplate = "%{y:,.0s}",
    increasing = {"marker":{"color":"#2ecc71"}},
    decreasing = {"marker":{"color":"#e74c3c"}},
    totals = {"marker":{"color":"#3498db"}}
))
st.plotly_chart(fig_wf, use_container_width=True)

# 7. ТАБЛИЦЯ P&L (КОЛЬОРИ ТА ПРИБУТОК ПЕРШИМ РЯДКОМ)
st.divider()
st.subheader("📑 Звіт P&L за місяцями")

df['Month'] = df['Date'].dt.strftime('%m-%Y')
sorted_months = sorted(df['Month'].unique(), key=lambda x: pd.to_datetime(x, format='%m-%Y'))

pnl = df.pivot_table(index=['Type', 'Group', 'Category'], columns='Month', values='Amount', aggfunc='sum')
pnl = pnl[sorted_months]

# Розрахунок прибутку
profit_row = pnl.loc['1. ПРИХОДИ'].sum() - pnl.loc['2. ВИТРАТИ'].sum()
profit_df = pd.DataFrame([profit_row], index=pd.MultiIndex.from_tuples([('0. РЕЗУЛЬТАТ', 'Total', 'ЧИСТИЙ ПРИБУТОК')], names=['Type', 'Group', 'Category']))
profit_df.columns = pnl.columns

# Об'єднання
pnl_final = pd.concat([profit_df, pnl]).sort_index()

# ФУНКЦІЯ СТИЛІЗАЦІЇ
def apply_styles(styler):
    # 1. Чистий прибуток (Верхній рядок - Синій)
    styler.apply(lambda x: ['background-color: #3498db; color: white; font-weight: bold' if x.name[0] == '0. РЕЗУЛЬТАТ' else '' for _ in x], axis=1)
    
    # 2. Податки (Контрастне виділення - Темно-червоний)
    styler.apply(lambda x: ['background-color: #b71c1c; color: white; font-weight: bold' if x.name[1] == 'Taxes' else '' for _ in x], axis=1)
    
    # 3. Доходи (Зелено-блакитний градієнт GnBu)
    styler.background_gradient(cmap='GnBu', subset=pd.IndexSlice[('1. ПРИХОДИ', slice(None), slice(None)), :])
    
    # 4. Витрати (Жовто-червоний градієнт YlOrRd)
    styler.background_gradient(cmap='YlOrRd', subset=pd.IndexSlice[('2. ВИТРАТИ', ['Fixed', 'Variable'], slice(None)), :])
    
    return styler

st.dataframe(apply_styles(pnl_final.style.format("{:,.0f}")), use_container_width=True)

# Кнопка завантаження
csv = pnl_final.to_csv().encode('utf-8-sig')
st.download_button(
    label="📥 Завантажити повний звіт у CSV (Excel)",
    data=csv,
    file_name='SapiensFin_Full_Report.csv',
    mime='text/csv'
)

# 8. CASH FLOW
st.divider()
st.subheader("📉 Прогноз руху грошових коштів (Cash Flow)")

df_cf = df.copy()
if ar_delay > 0:
    df_cf.loc[df_cf['Type'] == '1. ПРИХОДИ', 'Date'] += pd.Timedelta(days=ar_delay)

df_cf['Net'] = df_cf.apply(lambda x: x['Amount'] if 'ПРИХОДИ' in x['Type'] else -x['Amount'], axis=1)
daily_cf = df_cf.groupby('Date')['Net'].sum().sort_index().reset_index()
daily_cf['Balance'] = init_bal + daily_cf['Net'].cumsum()

fig_cf = go.Figure()
fig_cf.add_trace(go.Scatter(x=daily_cf['Date'], y=daily_cf['Balance'], fill='tozeroy', line_color='#2E86C1', name="Залишок на рахунку"))
fig_cf.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="Касовий розрив")
st.plotly_chart(fig_cf, use_container_width=True)

if daily_cf['Balance'].min() < 0:
    st.error(f"🚨 Виявлено ризик касового розриву: {abs(daily_cf['Balance'].min()):,.0f} PLN. Необхідно залучити обігові кошти.")
else:
    st.success("✅ Обігових коштів достатньо для стабільної роботи.")
