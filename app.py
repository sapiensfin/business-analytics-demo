import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Налаштування сторінки
st.set_page_config(page_title="SapiensFin | Demo", layout="wide")

# --- 1. ГЕНЕРАЦІЯ ДАНИХ (12 МІСЯЦІВ З КАСОВИМ РОЗРИВОМ) ---
def get_demo_data():
    data = []
    months = [f"2025-{m:02d}" for m in range(1, 13)]
    
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

    for m in months:
        month_num = int(m.split('-')[1])
        
        # Моделюємо касовий розрив: падіння виручки у березні (03) та жовтні (10)
        revenue_factor = 0.6 if month_num in [3, 10] else 1.0
        repair_factor = 3.5 if month_num in [3, 10] else 1.0
        
        # Доходи
        data.append({'Дата': f'{m}-05', 'Тип': '1. ПРИХОДИ', 'Стаття': 'Виручка (B2B)', 'Сума': 600000 * revenue_factor})
        
        # Витрати
        for cat, amt in expense_categories.items():
            val = amt
            if cat == 'Ремонт та сервіс': val *= repair_factor
            data.append({'Дата': f'{m}-15', 'Тип': '2. ВИТРАТИ', 'Стаття': cat, 'Сума': val})
            
    return pd.DataFrame(data)

# --- 2. БІЧНА ПАНЕЛЬ (BRANDING & CONTROLS) ---
with st.sidebar:
    st.markdown("### Sapiens Fin")
    st.markdown("[sapiensfin.eu](https://sapiensfin.eu)")
    st.write("---")
    st.header("🕹️ Симулятор рішень")
    inc_change = st.slider("Зміна доходу (%)", -20, 40, 0)
    exp_opt = st.slider("Оптимізація витрат (%)", -30, 0, 0)
    init_bal = st.number_input("Стартовий капітал (PLN)", value=100000)
    st.write("---")
    st.caption("Демо-модель для стратегічного планування")

# --- 3. ОБРОБКА ТА СИМУЛЯЦІЯ ---
df = get_demo_data()
df['Дата'] = pd.to_datetime(df['Дата'])
df['Сума'] = pd.to_numeric(df['Сума'])

# Усі фільтри тепер суворо кириличні
df.loc[df['Тип'] == '1. ПРИХОДИ', 'Сума'] *= (1 + inc_change / 100)
df.loc[df['Тип'] == '2. ВИТРАТИ', 'Сума'] *= (1 + exp_opt / 100)

df['Місяць'] = df['Дата'].dt.strftime('%m-%Y')

# --- 4. ГОЛОВНИЙ ЕКРАН ---
st.title("Financial Strategy Demo")
st.markdown("Інтелектуальні системи аналітики")

# Метрики
income_total = df[df['Тип'] == '1. ПРИХОДИ']['Сума'].sum()
expense_total = df[df['Тип'] == '2. ВИТРАТИ']['Сума'].sum()
net_profit = income_total - expense_total

c1, c2, c3 = st.columns(3)
c1.metric("Річний оборот", f"{income_total:,.0f} PLN")
c2.metric("Чистий прибуток", f"{net_profit:,.0f} PLN")
c3.metric("Рентабельність", f"{(net_profit/expense_total*100):.1f}%")

# --- 5. ТАБЛИЦЯ P&L (БІЗНЕС-АНАЛІТИКА) ---
st.subheader("📑 Річний звіт P&L")
pnl = df.pivot_table(index=['Тип', 'Стаття'], columns='Місяць', values='Сума', aggfunc='sum', sort=False)

st.dataframe(
    pnl.style.format("{:,.0f}")
    .background_gradient(cmap='GnBu', subset=pd.IndexSlice[('1. ПРИХОДИ', slice(None)), :])
    .background_gradient(cmap='YlOrRd', subset=pd.IndexSlice[('2. ВИТРАТИ', slice(None)), :]),
    use_container_width=True
)

# --- 6. CASH FLOW ГРАФІК ---
st.divider()
st.subheader("📉 Прогноз руху грошових коштів (Cash Flow)")

df = df.sort_values('Дата')
df['Зміна'] = df.apply(lambda x: x['Сума'] if 'ПРИХОДИ' in x['Тип'] else -x['Сума'], axis=1)
df['Залишок'] = init_bal + df['Зміна'].cumsum()

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=df['Дата'], y=df['Залишок'], 
    mode='lines', fill='tozeroy', 
    line=dict(color='#4A90E2', width=4),
    fillcolor='rgba(74, 144, 226, 0.1)',
    name='Баланс'
))

# Лінія касового розриву
fig.add_hline(y=0, line_dash="dash", line_color="#E74C3C", line_width=2)
fig.update_layout(xaxis_title="2025 рік", yaxis_title="Баланс (PLN)", height=500)
st.plotly_chart(fig, use_container_width=True)

# Динамічний аналіз
min_bal = df['Залишок'].min()
if min_bal < 0:
    st.error(f"🚨 Виявлено касовий розрив: {abs(min_bal):,.0f} PLN")
else:
    st.success("✅ Модель стійка. Для детального аудиту вашого бізнесу завітайте на sapiensfin.eu")

st.markdown("---")
st.markdown(f"### [Отримати консультацію на sapiensfin.eu](https://sapiensfin.eu)")

