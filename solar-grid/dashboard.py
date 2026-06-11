"""Dashboard Streamlit pentru analiza solar grid.

Interfata peste motorul de metrici din simulation.py (clasele de sectiuni).
Ruleaza:  streamlit run dashboard.py
"""
import streamlit as st
import plotly.express as px

import simulation as sim

st.set_page_config(page_title="Solar Grid - Analiza energetica",
                   page_icon="☀️", layout="wide")

# ordine luni pentru sortarea graficelor
LUNI = ["January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"]


@st.cache_data
def get_data():
    """Incarca datele Gold din SQLite (cache - se citeste o singura data)."""
    return sim.load_gold()


gold = get_data()
gen = gold["gold_generation_vs_consumption"]
anomalii = gold["gold_anomalii_grid"]

# instantiem motoarele de metrici o data
sd = sim.SurplusDeficitMetrics(gen)
gp = sim.GenerationPerformanceMetrics(gen)
mm = sim.MismatchMetrics(gen)

# ---------------- Sidebar ----------------
st.sidebar.title("Filtre")
zone_toate = sorted(gen["zona_electrica"].unique())
zone_sel = st.sidebar.multiselect("Zone electrice", zone_toate, default=zone_toate)
if not zone_sel:
    st.warning("Selecteaza cel putin o zona.")
    st.stop()

# ---------------- Header ----------------
st.title("☀️ Solar Grid — Analiza energetica 2024")
st.caption("Date Gold (Databricks → SQLite local) · 6 zone electrice · granularitate lunara")

# ---------------- Sectiunea 1: Deficit / Surplus ----------------
st.header("1 · Deficit / Surplus energetic (anual, pe zona)")

s1 = sd.summary()
s1 = s1[s1["zona_electrica"].isin(zone_sel)].copy()
# self-sufficiency ratio (0-1) = coverage_pct/100, forma raport (NU Performance Ratio PV)
s1["self_suff_ratio"] = (s1["coverage_pct"] / 100).round(3)

c1, c2, c3 = st.columns(3)
c1.metric(f'Cea mai autonoma — {s1.iloc[0]["zona_electrica"]}',
          f'{s1.iloc[0]["coverage_pct"]:.0f}%', help="grad de acoperire din productie proprie")
c2.metric(f'Cea mai dependenta — {s1.iloc[-1]["zona_electrica"]}',
          f'{s1.iloc[-1]["coverage_pct"]:.0f}%', help="grad de acoperire din productie proprie")
c3.metric("Zone in deficit anual", f'{(s1["balanta_neta_kwh"] < 0).sum()} / {len(s1)}')

col_a, col_b = st.columns([3, 2])
with col_a:
    fig = px.bar(s1, x="zona_electrica", y="coverage_pct",
                 title="Grad de acoperire (% consum acoperit din productie proprie)",
                 labels={"coverage_pct": "Acoperire %", "zona_electrica": "Zona"},
                 color="coverage_pct", color_continuous_scale="RdYlGn")
    fig.add_hline(y=100, line_dash="dash", annotation_text="echilibru (100%)")
    st.plotly_chart(fig, use_container_width=True)
with col_b:
    st.dataframe(s1, use_container_width=True, hide_index=True)

# ---------------- Sectiunea 2: Indici lunari ----------------
st.header("2 · Indici lunari — consum / productie / performanta")

s2 = gp.summary()
s2 = s2[s2["zona_electrica"].isin(zone_sel)]
s2["luna_nume"] = s2["luna_nume"].astype("category").cat.set_categories(LUNI, ordered=True)
s2 = s2.sort_values(["zona_electrica", "luna_nume"])

metric = st.radio("Index de afisat", ["perf_idx", "consum_idx", "prod_idx", "mismatch"],
                  horizontal=True,
                  format_func=lambda x: {"perf_idx": "Performanta (acoperire)",
                                         "consum_idx": "Consum", "prod_idx": "Productie",
                                         "mismatch": "Mismatch"}[x])
fig2 = px.line(s2, x="luna_nume", y=metric, color="zona_electrica", markers=True,
               labels={"luna_nume": "Luna", metric: metric})
if metric == "perf_idx":
    fig2.add_hline(y=100, line_dash="dash", annotation_text="acoperire completa")
if metric == "mismatch":
    fig2.add_hline(y=0, line_dash="dash", annotation_text="echilibru sezonier")
st.plotly_chart(fig2, use_container_width=True)

st.info("**Mismatch** = index_productie − index_consum. Pozitiv vara (supraproductie), "
        "negativ iarna (presiune pe retea), ~0 toamna (echilibru). Masoara *cand* "
        "produci vs *cand* consumi, nu cantitatea (kWh).")

# ---------------- Sectiunea 3: Mismatch ----------------
st.header("3 · Mismatch sezonier — cine conduce decalajul")

col_c, col_d = st.columns(2)
with col_c:
    drv = mm.drivers()
    drv = drv[drv["zona_electrica"].isin(zone_sel)]
    drv_long = drv.melt(id_vars="zona_electrica",
                        value_vars=["amp_productie", "amp_consum"],
                        var_name="tip", value_name="amplitudine")
    figd = px.bar(drv_long, x="zona_electrica", y="amplitudine", color="tip",
                  barmode="group",
                  title="Amplitudine sezoniera: productia conduce (~5.5x consumul)")
    figd.update_layout(xaxis_title=None)
    st.plotly_chart(figd, use_container_width=True)
with col_d:
    monthly = mm.monthly()
    monthly = monthly[monthly["zona_electrica"].isin(zone_sel)]
    monthly["luna_nume"] = monthly["luna_nume"].astype("category").cat.set_categories(LUNI, ordered=True)
    pivot = monthly.pivot_table(index="luna_nume", columns="zona_electrica",
                                values="mismatch", observed=False)
    figh = px.imshow(pivot, color_continuous_scale="RdBu", aspect="auto",
                     origin="upper", title="Heatmap mismatch (luna × zona)",
                     labels={"color": "mismatch"})
    figh.update_layout(xaxis_title=None, yaxis_title=None)
    st.plotly_chart(figh, use_container_width=True)

st.subheader("Luna de echilibru vs luna de extrem")
ext = mm.extremes()
ext = ext[ext["zona_electrica"].isin(zone_sel)]
st.dataframe(ext, use_container_width=True, hide_index=True)

# ---------------- Sectiunea 4: Profil intraday orar ----------------
st.header("4 · Profil intraday — orar (6-19)")
st.caption("Date din gold_anomalii_grid: doar orele 6-19, doar randuri de DEFICIT. "
           "Nu e profil zi/noapte complet — e profilul de zi.")

ip = sim.IntradayProfile(anomalii[anomalii["zona_electrica"].isin(zone_sel)])
h = ip.hourly_avg()
pk = ip.peak_hours()

m1, m2, m3 = st.columns(3)
m1.metric("Varf productie", f'ora {pk["varf_productie"]}')
m2.metric("Varf consum", f'ora {pk["varf_consum"]}')
m3.metric("Acoperire maxima", f'{pk["acoperire_maxima_pct"]:.0f}%',
          help="nici la varf de soare productia nu acopera consumul")

col_e, col_f = st.columns(2)
with col_e:
    fige = px.line(h, x="ora", y=["productie", "consum"], markers=True,
                   title="Productie vs consum mediu pe ora (kWh)")
    fige.update_layout(yaxis_title="kWh", legend_title=None)
    st.plotly_chart(fige, use_container_width=True)
with col_f:
    figc = px.bar(h, x="ora", y="acoperire_pct",
                  title="Acoperire orara (% consum acoperit)",
                  color="acoperire_pct", color_continuous_scale="RdYlGn")
    figc.update_layout(yaxis_title="acoperire %")
    st.plotly_chart(figc, use_container_width=True)

st.info("Consumul are **doua varfuri** (dimineata 7-9 si seara 18-19, cand lumea se "
        "trezeste / se intoarce acasa) fix cand soarele e slab. La pranz productia "
        "e maxima dar tot sub 50% acoperire. De-aia solarul singur nu ajunge.")
