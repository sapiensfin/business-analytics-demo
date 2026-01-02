import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Налаштування сторінки
st.set_page_config(page_title="SapiensFin | Professional Demo", layout="wide")

# --- 1. ГЕНЕРАЦІЯ ДАНИХ ---
@st.cache_data
def get_base_data():
    data = []
    months = pd.date_range(start="2025-01-01", periods=12, freq='MS')
    
    expense_categories = {
        'Оренда та склад': 55000,
        'Зарплата офіс': 65000,
        'Зарплата водії': 180000,
        'ПММ (Паливо)': 95000,
        'Лізинг авто': 75000,
        'Ремонт та сервіс': 25000,
        'Маркетинг': 20000,
        'Податки та збори': 55000,
        'Амортизація': 10000
    }

    for month in months:
        month_num = month.month
        # Сезонність: березень та жовтень складні місяці
        revenue_factor = 0.6 if month_num in [3, 10] else 1.0
        repair_factor = 3.5 if month_num in [3, 10] else 1.0
        
        data.append({'Дата': month, 'Тип': '1. ПРИХОДИ', 'Стаття': 'Виручка (B2B)', 'Сума': 600000 * revenue_factor})
        
        for cat, amt in expense_categories.items():
            val = amt
            if cat == 'Ремонт та сервіс': val *= repair_factor
            data.append({'Дата': month, 'Тип': '2. ВИТРАТИ', 'Стаття': cat, 'Сума': val})
            
    return pd.DataFrame(data)

# --- 2. БІЧНА ПАНЕЛЬ ---
with st.sidebar:
    st.markdown("### 🚀 Sapiens Fin")
    st.markdown("[sapiensfin.eu](https://sapiensfin.eu)")
    st.write("---")
    st.header("🕹️ Симулятор рішень")
    
    price_inc = st.slider("Збільшення цін (%)", 0, 50, 0)
    cost_red = st.slider("Оптимізація витрат (%)", 0, 50, 0)
    init_bal = st.number_input("Стартовий капітал (PLN)", value=100000)
    
    st.write("---")
    st.caption("Змінюйте параметри, щоб побачити прогноз розвитку бізнесу.")

# --- 3. ОБРОБКА ДАНИХ ---
df_base = get_base_data()
df = df_base.copy()

# Базові показники для дельти
base_inc = df_base[df_base['Тип'] == '1. ПРИХОДИ']['Сума'].sum()
base_exp = df_base[df_base['Тип'] == '2. ВИТРАТИ']['Сума'].sum()
base_profit = base_inc - base_exp

# Застосування слайдерів
df.loc[df['Тип'] == '1. ПРИХОДИ', 'Сума'] *= (1 + price_inc / 100)
df.loc[df['Тип'] == '2. ВИТРАТИ', 'Сума'] *= (1 - cost_red / 100)

df['Місяць_Назва'] = df['Дата'].dt.strftime('%m-%Y')

# Розрахунок метрик
income_total = df[df['Тип'] == '1. ПРИХОДИ']['Сума'].sum()
expense_total = df[df['Тип'] == '2. ВИТРАТИ']['Сума'].sum()
net_profit = income_total - expense_total
ros = (net_profit / income_total * 100) if income_total > 0 else 0

# --- 4. ГОЛОВНИЙ ЕКРАН ---
st.title("Financial Strategy Dashboard")

c1, c2, c3 = st.columns(3)
c1.metric("Річний оборот", f"{income_total:,.0f} PLN", f"{income_total - base_inc:,.1f}")
c2.metric("Чистий прибуток", f"{net_profit:,.0f} PLN", f"{net_profit - base_profit:,.1f}")
c3.metric("Рентабельність (ROS)", f"{ros:.1f}%", f"{ros - (base_profit/base_inc*100):.1f}%")

# --- 5. WATERFALL CHART ---
st.divider()
st.subheader("💎 Трансформація доходу в прибуток")
expenses_by_cat = df[df['Тип'] == '2. ВИТРАТИ'].groupby('Стаття')['Сума'].sum().sort_values(ascending=False)

fig_wf = go.Figure(go.Waterfall(
    measure = ["relative"] * (len(expenses_by_cat) + 1) + ["total"],
    x = ["Виручка"] + list(expenses_by_cat.index) + ["Прибуток"],
    y = [income_total] + [-v for v in expenses_by_cat.values] + [0],
    connector = {"line":{"color":"rgba(63, 63, 63, 0.5)"}},
))
fig_wf.update_layout(height=400)
st.plotly_chart(fig_wf, use_container_width=True)

# --- 6. КРУГОВІ ДІАГРАМИ (ПОРІВНЯННЯ) ---
st.divider()
st.subheader("📊 Структура витрат: Початок vs Кінець року")
col_pie1, col_pie2 = st.columns(2)

for i, col in enumerate([col_pie1, col_pie2]):
    target_month = 1 if i == 0 else 12
    title = "Січень" if i == 0 else "Грудень"
    exp_data = df[(df['Тип'] == '2. ВИТРАТИ') & (df['Дата'].dt.month == target_month)]
    
    fig = go.Figure(data=[go.Pie(labels=exp_data['Стаття'], values=exp_data['Сума'], hole=.4)])
    fig.update_layout(title=title, height=350, margin=dict(t=30, b=0, l=0, r=0))
    col.plotly_chart(fig, use_container_width=True)

# --- 7. ТАБЛИЦЯ P&L ---
st.divider()
st.subheader("📑 Звіт про прибутки та збитки (P&L)")
# Виправлено помилку 'Sum' -> 'Сума'
pnl = df.pivot_table(index=['Тип', 'Стаття'], columns='Місяць_Назва', values='Сума', aggfunc='sum', sort=False)
pnl_cols = df.sort_values('Дата')['Місяць_Назва'].unique()
pnl = pnl[pnl_cols]

st.dataframe(
    pnl.style.format("{:,.0f}")
    .background_gradient(cmap='Greens', subset=pd.IndexSlice[('1. ПРИХОДИ', slice(None)), :])
    .background_gradient(cmap='Reds', subset=pd.IndexSlice[('2. ВИТРАТИ', slice(None)), :]),
    use_container_width=True
)

# --- 8. CASH FLOW ГРАФІК ---
st.divider()
st.subheader("📉 Прогноз Cash Flow (Залишки на рахунках)")
df_cf = df.sort_values('Дата').copy()
df_cf['Зміна'] = df_cf.apply(lambda x: x['Сума'] if 'ПРИХОДИ' in x['Тип'] else -x['Сума'], axis=1)
daily_bal = df_cf.groupby('Дата')['Зміна'].sum().reset_index()
daily_bal['Залишок'] = init_bal + daily_bal['Зміна'].cumsum()

fig_cf = go.Figure()
fig_cf.add_trace(go.Scatter(x=daily_bal['Дата'], y=daily_bal['Залишок'], mode='lines', fill='tozeroy', line=dict(color='#00CC96')))
fig_cf.add_hline(y=0, line_dash="dash", line_color="red")
st.plotly_chart(fig_cf, use_container_width=True)

min_bal = daily_bal['Залишок'].min()
if min_bal < 0:
    st.error(f"🚨 Касовий розрив: {abs(min_bal):,.0f} PLN. Потрібне фінансування!")
else:
    st.success(f"✅ Модель стійка. Мінімальний залишок: {min_bal:,.0f} PLN")
