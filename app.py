
import streamlit as st
import matplotlib.pyplot as plt
import os

try:
    from openai import OpenAI
    OPENAI_OK = True
except Exception:
    OPENAI_OK = False

st.set_page_config(page_title="Smart Water Calc v3", page_icon="💧", layout="wide")
st.title("💧 Smart Water Calc v3 — Айлық норма, төлем және автоматты ЖИ кеңес")
st.caption("Мектеп оқушыларына арналған интерактивті экоқұрал (қазақ тілінде)")

DAILY_NORM_PER_PERSON_L = 140.0
BASE_TARIFF_TENGE_PER_M3 = 30.0
EXCESS_TARIFF_TENGE_PER_M3 = 611.0

st.sidebar.header("Параметрлер")
people = st.sidebar.number_input("Үйдегі адам саны", min_value=1, value=5, step=1)
days_in_month = st.sidebar.number_input("Айдағы күн саны", min_value=1, value=30, step=1)
unit = st.sidebar.selectbox("Айлық тұтыну өлшемі", ["литр (L)", "текше метр (m³)"])

if unit == "литр (L)":
    cons_in = st.sidebar.number_input("Ай ішіндегі нақты тұтыну (л)", min_value=0.0, value=50000.0, step=100.0)
    cons_l = cons_in
else:
    cons_in = st.sidebar.number_input("Ай ішіндегі нақты тұтыну (м³)", min_value=0.0, value=50.0, step=1.0)
    cons_l = cons_in * 1000.0

monthly_norm_l = DAILY_NORM_PER_PERSON_L * people * days_in_month
within_l = min(cons_l, monthly_norm_l)
excess_l = max(0.0, cons_l - monthly_norm_l)
saved_l = max(0.0, monthly_norm_l - cons_l)

total_cost = (within_l/1000.0) * BASE_TARIFF_TENGE_PER_M3 + (excess_l/1000.0) * EXCESS_TARIFF_TENGE_PER_M3
saved_cost = (saved_l/1000.0) * BASE_TARIFF_TENGE_PER_M3

c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("Айлық норма (л)", f"{monthly_norm_l:,.0f}".replace(",", " "))
with c2: st.metric("Нақты тұтыну (л)", f"{cons_l:,.0f}".replace(",", " "))
with c3: st.metric("Артық/Үнем (л)", f"{(excess_l if excess_l>0 else -saved_l):,.0f}".replace(",", " "))
with c4: st.metric("Жалпы төлем (₸)", f"{total_cost:,.2f}".replace(",", " "))

st.subheader("Толық есеп")
st.write(f"- Адам саны: {people}")
st.write(f"- Айдағы күн саны: {days_in_month}")
st.write(f"- Норма ішіндегі тариф: {BASE_TARIFF_TENGE_PER_M3:.0f} ₸/м³")
st.write(f"- Артық тұтыну тарифі: {EXCESS_TARIFF_TENGE_PER_M3:.0f} ₸/м³")
st.write(f"- Норма шегіндегі тұтыну: {within_l:,.0f} л → {(within_l/1000.0)*BASE_TARIFF_TENGE_PER_M3:,.2f} ₸".replace(",", " "))
st.write(f"- Артық тұтыну: {excess_l:,.0f} л → {(excess_l/1000.0)*EXCESS_TARIFF_TENGE_PER_M3:,.2f} ₸".replace(",", " "))

if saved_l > 0:
    st.success(f"✅ Нормадан {saved_l:,.0f} л аз → шамамен {saved_cost:,.2f} ₸ үнем.".replace(",", " "))

st.subheader("Графиктер")
fig1, ax1 = plt.subplots()
ax1.bar(["Айлық норма", "Нақты тұтыну"], [monthly_norm_l/1000.0, cons_l/1000.0])
ax1.set_ylabel("Көлем (м³)")
ax1.set_title("Айлық норма мен нақты тұтыну (м³)")
st.pyplot(fig1)

fig2, ax2 = plt.subplots()
labels, values = [], []
if saved_l > 0:
    labels.append("Үнем (л)"); values.append(saved_l)
if excess_l > 0:
    labels.append("Артық (л)"); values.append(excess_l)
if not labels:
    labels = ["Айырма жоқ"]; values = [0]
ax2.bar(labels, values)
ax2.set_ylabel("Литр")
ax2.set_title("Нормадан ауытқу")
st.pyplot(fig2)

st.subheader("ЖИ кеңесі (автоматты)")
if OPENAI_OK:
    api_key = st.secrets.get("OPENAI_API_KEY") if "OPENAI_API_KEY" in st.secrets else os.getenv("OPENAI_API_KEY")
    if api_key:
        try:
            client = OpenAI(api_key=api_key)
            context = (
                f"Адам саны: {people}\n"
                f"Айдағы күн саны: {days_in_month}\n"
                f"Айлық норма (л): {int(monthly_norm_l)}\n"
                f"Нақты тұтыну (л): {int(cons_l)}\n"
                f"Артық тұтыну (л): {int(excess_l)}\n"
                f"Үнемделген су (л): {int(saved_l)}\n"
                f"Жалпы төлем (₸): {total_cost:.2f}"
            )
            prompt = (
                "Төмендегі су тұтыну мәліметтеріне сүйеніп, қазақ тілінде 5–6 сөйлемнен тұратын тиянақты кеңес жаз. "
                "Қысқаша қорытынды беріп, нақты үнемдеу тәсілдерін ұсын. Сөйлемдер жылы әрі түсінікті болсын.\n\n"
                + context
            )
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            st.write(resp.choices[0].message.content)
        except Exception as e:
            st.info(f"ЖИ кеңесін алу мүмкін болмады: {e}")
    else:
        st.info("ЖИ кеңесін көру үшін Secrets → OPENAI_API_KEY орнатыңыз.")
else:
    st.info("OpenAI кітапханасы орнатылмаған. requirements.txt арқылы орнатыңыз.")

st.markdown("---")
st.caption("© 2025 Smart Water Calc v3 | Қазақ тіліндегі автоматты ЖИ кеңесі")
