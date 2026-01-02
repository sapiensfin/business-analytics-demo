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
        revenue_factor = 0.6 if month_num in [3, 10] else 1.0
        repair_factor = 3.5 if month_num in [3, 10] else 1.0
        
        # Доходи
        data.append({'Дата': month, 'Тип': '1. ПРИХОДИ', 'Стаття': 'Виручка (B2B)', 'Сума': 600000 * revenue_factor})
        
        # Витрати
        for cat, amt in expense_categories.items():
            val = amt
            if cat == 'Ремонт та сервіс': val *= repair_factor
            data.append({'Дата': month, 'Тип': '2. ВИТРАТИ', 'Стаття': cat, 'Сума': val})
            
    return pd.DataFrame(data)

# --- 2. БІЧНА ПАНЕЛЬ ---
with st.sidebar:
    st.image("https://via.placeholder.com/150x50?text=Sapiens+Fin", use_container_width=True)
    st.markdown("### [sapiensfin.eu](https://sapiensfin.eu)")
    st.write("---")
    st.header("🕹️ Симулятор рішень")
    
    price_inc = st.slider("Збільшення цін (%)", 0, 50, 0)
    cost_red = st.slider("Оптимізація витрат (%)", 0, 50, 0)
    init_bal = st.number_input("Стартовий капітал (PLN)", value=100000, step=10000)
    
    st.write("---")
    st.info("Ця модель дозволяє миттєво побачити вплив управлінських рішень на P&L та Cash Flow.")

# --- 3. ОБРОБКА ДАНИХ ---
df_base = get_base_data()
df = df_base.copy()

# Розрахунок базових метрик (без слайдерів) для порівняння
base_inc = df_base[df_base['Тип'] == '1. ПРИХОДИ']['Сума'].sum()
base_exp = df_base[df_base['Тип'] == '2. ВИТРАТИ']['Сума'].sum()
base_profit = base_inc - base_exp

# Застосовуємо симуляцію
df.loc[df['Тип'] == '1. ПРИХОДИ', 'Сума'] *= (1 + price_inc / 100)
df.loc[df['Тип'] == '2. ВИТРАТИ', 'Сума'] *= (1 - cost_red / 100)

df['Місяць_Назва'] = df['Дата'].dt.strftime('%b %Y')

# Розрахунок нових метрик
income_total = df[df['Тип'] == '1. ПРИХОДИ']['Сума'].sum()
expense_total = df[df['Тип'] == '2. ВИТРАТИ']['Сума'].sum()
net_profit = income_total - expense_total
ros = (net_profit / income_total * 100) if income_total > 0 else 0

# --- 4. ГОЛОВНИЙ ЕКРАН ---
st.title("📊 Financial Strategy Dashboard")
st.markdown("Моделювання стану **TO-BE** на основі ваших управлінських гіпотез")

# Метрики з Delta
c1, c2, c3 = st.columns(3)
c1.metric("Річний оборот", f"{income_total:,.0f} PLN", f"{income_total - base_inc:,.0f} PLN")
c2.metric("Чистий прибуток", f"{net_profit:,.0f} PLN", f"{net_profit - base_profit:,.0f} PLN")
c3.metric("Рентабельність (ROS)", f"{ros:.1f}%", f"{ros - (base_profit/base_inc*100):.1f}%")

# --- 5. WATERFALL CHART (СТРУКТУРА ПРИБУТКУ) ---
st.divider()
st.subheader("💎 Формування чистого прибутку (Waterfall)")

wf_data = df.groupby('Стаття')['Сума'].sum()
revenue_val = df[df['Тип'] == '1. ПРИХОДИ']['Сума'].sum()
expenses_by_cat = df[df['Тип'] == '2. ВИТРАТИ'].groupby('Стаття')['Сума'].sum()

fig_wf = go.Figure(go.Waterfall(
    name = "P&L", orientation = "v",
    measure = ["relative"] * (len(expenses_by_cat) + 1) + ["total"],
    x = ["Виручка"] + list(expenses_by_cat.index) + ["Чистий прибуток"],
    textposition = "outside",
    text = [f"-{v:,.0f}" if i > 0 else f"{v:,.0f}" for i, v in enumerate([revenue_val] + list(expenses_by_cat.values))],
    y = [revenue_val] + [-v for v in expenses_by_cat.values] + [0],
    connector = {"line":{"color":"rgb(63, 63, 63)"}},
))

fig_wf.update_layout(height=500, showlegend=False)
st.plotly_chart(fig_wf, use_container_width=True)

# --- 6. ТАБЛИЦЯ P&L ТА ЕКСПОРТ ---
st.divider()
col_title, col_btn = st.columns([4, 1])
col_title.subheader("📑 Детальний звіт P&L за місяцями")

pnl = df.pivot_table(index=['Тип', 'Стаття'], columns='Місяць_Назва', values='Sum', aggfunc='sum', sort=False)
# Сортуємо колонки згідно з хронологією
pnl = pnl[df['Місяць_Назва'].unique()]

st.dataframe(pnl.style.format("{:,.0f}"), use_container_width=True)

csv = df.to_csv(index=False).encode('utf-8')
col_btn.download_button("📥 Скачати Excel/CSV", data=csv, file_name="sapiens_fin_model.csv", mime="text/csv")

# --- 7. CASH FLOW ГРАФІК ---
st.divider()
st.subheader("📉 Прогноз залишків на рахунках (Cash Flow)")

df_cf = df.sort_values('Дата').copy()
df_cf['Зміна'] = df_cf.apply(lambda x: x['Сума'] if 'ПРИХОДИ' in x['Тип'] else -x['Сума'], axis=1)
# Агрегуємо по датах для графіку балансу
daily_bal = df_cf.groupby('Дата')['Зміна'].sum().reset_index()
daily_bal['Залишок'] = init_bal + daily_bal['Зміна'].cumsum()

fig_cf = go.Figure()
fig_cf.add_trace(go.Scatter(
    x=daily_bal['Дата'], y=daily_bal['Залишок'], 
    mode='lines+markers', fill='tozeroy', 
    line=dict(color='#2ECC71', width=3),
    fillcolor='rgba(46, 204, 113, 0.1)',
    name='Прогноз залишку'
))

fig_cf.add_hline(y=0, line_dash="dash", line_color="#E74C3C", annotation_text="Критична межа")
st.plotly_chart(fig_cf, use_container_width=True)

# Аналіз розриву
min_bal = daily_bal['Залишок'].min()
if min_bal < 0:
    st.error(f"⚠️ **Увага:** Ризик касового розриву! Мінімальний залишок: {min_bal:,.0f} PLN. Необхідне залучення оборотних коштів.")
else:
    st.success(f"✅ Фінансова модель стійка. Мінімальний запас міцності: {min_bal:,.0f} PLN.")

st.markdown("<center style='margin-top:50px;'><p>Бажаєте таку модель для вашого бізнесу? <a href='https://sapiensfin.eu'>SapiensFin.eu</a></p></center>", unsafe_allow_html=True)
