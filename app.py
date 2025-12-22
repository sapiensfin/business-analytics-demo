import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Налаштування сторінки
st.set_page_config(page_title="SapiensFin | Demo Strategy", layout="wide")

# --- 1. ГЕНЕРАЦІЯ ДАНИХ (БАЗОВИЙ СТАН AS-IS) ---
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
        
        # Моделюємо сезонність та ризики для AS-IS (березень та жовтень — просадка)
        revenue_factor = 0.65 if month_num in [3, 10] else 1.0
        repair_factor = 3.5 if month_num in [3, 10] else 1.0
        
        # Доходи
        data.append({'Дата': f'{m}-05', 'Тип': '1. ПРИХОДИ', 'Стаття': 'Виручка (B2B)', 'Сума': 600000 * revenue_factor})
        
        # Витрати
        for cat, amt in expense_categories.items():
            val = amt
            if cat == 'Ремонт та сервіс': val *= repair_factor
            data.append({'Дата': f'{m}-15', 'Тип': '2. ВИТРАТИ', 'Стаття': cat, 'Сума': val})
            
    return pd.DataFrame(data)

# --- 2. БІЧНА ПАНЕЛЬ (КЕРУВАННЯ СТРАТЕГІЄЮ) ---
with st.sidebar:
    st.image("https://sapiensfin.eu/wp-content/uploads/2024/01/logo.png", width=200) # Якщо є лого
    st.markdown("### [sapiensfin.eu](https://sapiensfin.eu)")
    st.write("---")
    st.header("🕹️ Симулятор рішень (TO-BE)")
    
    # Нова логіка повзунків
    price_inc = st.slider("Збільшуємо ціни на (%)", 0, 50, 0, help="Підвищення маржинальності при тому ж обсязі продажів")
    cost_red = st.slider("Зменшуємо витрати на (%)", 0, 50, 0, help="Оптимізація завдяки автоматизації та прибиранню рутини")
    
    init_bal = st.number_input("Стартовий капітал (PLN)", value=80000)
    st.write("---")
    st.caption("Використовуйте повзунки, щоб побачити, як автоматизація процесів впливає на ваш капітал.")

# --- 3. ОБРОБКА ТА РОЗРАХУНОК TO-BE ---
df_asis = get_demo_data()
df_asis['Дата'] = pd.to_datetime(df_asis['Дата'])

df_tobe = df_asis.copy()

# Застосовуємо стратегію TO-BE
df_tobe.loc[df_tobe['Тип'] == '1. ПРИХОДИ', 'Сума'] *= (1 + price_inc / 100)
df_tobe.loc[df_tobe['Тип'] == '2. ВИТРАТИ', 'Сума'] *= (1 - cost_red / 100)

# Розрахунок Cash Flow для обох станів
def calculate_cf(df_input, start_bal):
    temp_df = df_input.sort_values('Дата').copy()
    temp_df['Зміна'] = temp_df.apply(lambda x: x['Сума'] if 'ПРИХОДИ' in x['Тип'] else -x['Сума'], axis=1)
    temp_df['Залишок'] = start_bal + temp_df['Зміна'].cumsum()
    return temp_df

df_asis_cf = calculate_cf(df_asis, init_bal)
df_tobe_cf = calculate_cf(df_tobe, init_bal)

# --- 4. ГОЛОВНИЙ ЕКРАН ---
st.title("Financial Strategy: AS-IS vs TO-BE")
st.markdown("Перевірте, як розумна оптимізація рятує бізнес від касових розривів.")

# Метрики (порівняння)
income_total = df_tobe[df_tobe['Тип'] == '1. ПРИХОДИ']['Су_ма'].sum() if 'Су_ма' in df_tobe else df_tobe[df_tobe['Тип'] == '1. ПРИХОДИ']['Сума'].sum()
expense_total = df_tobe[df_tobe['Тип'] == '2. ВИТРАТИ']['Сума'].sum()
net_profit = income_total - expense_total
profit_growth = net_profit - (df_asis[df_asis['Тип'] == '1. ПРИХОДИ']['Сума'].sum() - df_asis[df_asis['Тип'] == '2. ВИТРАТИ']['Сума'].sum())

c1, c2, c3 = st.columns(3)
c1.metric("Річна виручка (TO-BE)", f"{income_total:,.0f} PLN")
c2.metric("Чистий прибуток (TO-BE)", f"{net_profit:,.0f} PLN", delta=f"{profit_growth:,.0f} PLN")
c3.metric("Рентабельність витрат", f"{(net_profit/expense_total*100):.1f}%")

# --- 5. ГРАФІК ПОРІВНЯННЯ ---
st.divider()
st.subheader("📉 Прогноз Cash Flow: Реальний стан vs Оптимізований")

fig = go.Figure()

# Лінія AS-IS (як є зараз)
fig.add_trace(go.Scatter(
    x=df_asis_cf['Дата'], y=df_asis_cf['Залишок'], 
    mode='lines', name='Стан AS-IS (Без змін)',
    line=dict(color='#E74C3C', width=2, dash='dot')
))

# Лінія TO-BE (після впровадження рішень)
fig.add_trace(go.Scatter(
    x=df_tobe_cf['Дата'], y=df_tobe_cf['Залишок'], 
    mode='lines', fill='tozeroy', 
    name='Стан TO-BE (Оптимізація)',
    line=dict(color='#2ECC71', width=4),
    fillcolor='rgba(46, 204, 113, 0.1)'
))

# Межа касового розриву
fig.add_hline(y=0, line_dash="dash", line_color="#000", line_width=1)

fig.update_layout(
    xaxis_title="2025 рік", 
    yaxis_title="Баланс на рахунку (PLN)", 
    height=550,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)
st.plotly_chart(fig, use_container_width=True)

# Аналіз розривів
min_asis = df_asis_cf['Залишок'].min()
min_tobe = df_tobe_cf['Залишок'].min()

if min_tobe < 0:
    st.error(f"🚨 Навіть з поточною оптимізацією можливий розрив: {abs(min_tobe):,.0f} PLN. Спробуйте ще зменшити витрати.")
elif min_asis < 0 and min_tobe >= 0:
    st.success(f"🎉 Вітаємо! Оптимізація дозволила уникнути касового розриву в {abs(min_asis):,.0f} PLN.")
else:
    st.info("💡 Модель стабільна в обох варіантах, але TO-BE значно збільшує ваш капітал.")

# --- 6. ТАБЛИЦЯ P&L ---
with st.expander("📑 Переглянути детальний звіт P&L (TO-BE)"):
    df_tobe['Місяць'] = df_tobe['Дата'].dt.strftime('%m-%Y')
    pnl = df_tobe.pivot_table(index=['Тип', 'Стаття'], columns='Місяць', values='Сума', aggfunc='sum', sort=False)
    st.dataframe(pnl.style.format("{:,.0f}"), use_container_width=True)

st.markdown("---")
st.markdown(f"### [Забронювати аудит вашого бізнесу на sapiensfin.eu](https://sapiensfin.eu)")
