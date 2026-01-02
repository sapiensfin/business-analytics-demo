import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Налаштування
st.set_page_config(page_title="SapiensFin | Demo", layout="wide")

# 2. Очищення кешу (важливо для виправлення помилки)
st.cache_data.clear()

# 3. ГЕНЕРАЦІЯ ДАНИХ
@st.cache_data
def load_data():
    data = []
    months = pd.date_range(start="2025-01-01", periods=12, freq='MS')
    
    # Витрати
    exp_cats = {
        'Оренда': 55000, 'Зарплати': 245000, 'Паливо': 95000, 
        'Лізинг': 75000, 'Ремонт': 25000, 'Маркетинг': 20000
    }

    for m in months:
        m_num = m.month
        # Сезонність
        rev_f = 0.6 if m_num in [3, 10] else 1.0
        rep_f = 3.5 if m_num in [3, 10] else 1.0
        
        # ДОХІД
        data.append({'Date': m, 'Type': '1. ПРИХОДИ', 'Category': 'Виручка', 'Amount': float(600000 * rev_f)})
        
        # ВИТРАТИ
        for cat, amt in exp_cats.items():
            val = amt * rep_f if cat == 'Ремонт' else amt
            data.append({'Date': m, 'Type': '2. ВИТРАТИ', 'Category': cat, 'Amount': float(val)})
            
    return pd.DataFrame(data)

# 4. БІЧНА ПАНЕЛЬ
with st.sidebar:
    st.header("🕹️ Симулятор")
    p_inc = st.slider("Ріст цін (%)", 0, 50, 0)
    c_red = st.slider("Оптимізація витрат (%)", 0, 50, 0)
    st.write("---")
    st.markdown("[sapiensfin.eu](https://sapiensfin.eu)")

# 5. ОБРОБКА
df = load_data().copy()

# Застосовуємо симуляцію (використовуємо 'Amount')
df.loc[df['Type'] == '1. ПРИХОДИ', 'Amount'] *= (1 + p_inc / 100)
df.loc[df['Type'] == '2. ВИТРАТИ', 'Amount'] *= (1 - c_red / 100)

df['Month_Str'] = df['Date'].dt.strftime('%m-%Y')

# Метрики
total_inc = df[df['Type'] == '1. ПРИХОДИ']['Amount'].sum()
total_exp = df[df['Type'] == '2. ВИТРАТИ']['Amount'].sum()
profit = total_inc - total_exp

# 6. ВІДОБРАЖЕННЯ
st.title("Financial Strategy Dashboard")

m1, m2, m3 = st.columns(3)
m1.metric("Оборот", f"{total_inc:,.0f} PLN")
m2.metric("Прибуток", f"{profit:,.0f} PLN")
m3.metric("Рентабельність", f"{(profit/total_inc*100):.1f}%")

# 7. WATERFALL (Наглядно для власника)
st.divider()
st.subheader("💎 Waterfall: Від виручки до чистого прибутку")
exp_agg = df[df['Type'] == '2. ВИТРАТИ'].groupby('Category')['Amount'].sum().sort_values(ascending=False)

fig_wf = go.Figure(go.Waterfall(
    measure = ["relative"] * (len(exp_agg) + 1) + ["total"],
    x = ["Виручка"] + list(exp_agg.index) + ["Прибуток"],
    y = [total_inc] + [-v for v in exp_agg.values] + [0],
))
st.plotly_chart(fig_wf, use_container_width=True)

# 8. ПОРІВНЯННЯ СТРУКТУРИ (Кругові діаграми)
st.divider()
st.subheader("📊 Структура витрат: Початок vs Кінець року")
c_p1, c_p2 = st.columns(2)

for i, col in enumerate([c_p1, c_p2]):
    target_m = 1 if i == 0 else 12
    p_data = df[(df['Type'] == '2. ВИТРАТИ') & (df['Date'].dt.month == target_m)]
    fig = go.Figure(data=[go.Pie(labels=p_data['Category'], values=p_data['Amount'], hole=.4)])
    fig.update_layout(title="Січень" if i == 0 else "Грудень", height=380)
    col.plotly_chart(fig, use_container_width=True)

# 9. ТАБЛИЦЯ P&L (БЕЗ ПОМИЛОК)
st.divider()
st.subheader("📑 Звіт P&L за місяцями")

# Використовуємо ТОЧНІ назви стовпців: 'Type', 'Category', 'Month_Str', 'Amount'
pnl = df.pivot_table(
    index=['Type', 'Category'], 
    columns='Month_Str', 
    values='Amount', 
    aggfunc='sum'
)

# Хронологічне сортування
month_order = sorted(df['Month_Str'].unique(), key=lambda x: pd.to_datetime(x, format='%m-%Y'))
pnl = pnl[month_order]

st.dataframe(
    pnl.style.format("{:,.0f}").background_gradient(cmap='RdYlGn', axis=1), 
    use_container_width=True
)

# 10. CASH FLOW
st.divider()
st.subheader("📉 Прогноз залишків на рахунку")
df['Flow'] = df.apply(lambda x: x['Amount'] if 'ПРИХОДИ' in x['Type'] else -x['Amount'], axis=1)
daily_bal = df.groupby('Date')['Flow'].sum().reset_index()
daily_bal['Balance'] = 100000 + daily_bal['Flow'].cumsum()

st.line_chart(daily_bal.set_index('Date')['Balance'])
