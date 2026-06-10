"""
Garmin Solar Dashboard - Streamlit
Visualizes daily solar intensity from a Fenix 6X Pro Solar.

Run:
    cd "C:\\Power BI Projects\\PY Files\\garmin-solar"
    streamlit run app.py
"""

import os
import sqlite3
import subprocess
import sys

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DB_PATH = os.path.join(os.path.dirname(__file__), "garmin_solar.sqlite")

# Green palette
GREEN_BRIGHT = "#4cc406"
GREEN_MID = "#2fa30a"
GREEN_DEEP = "#1c6e06"
BG_DARK = "#080A0E"
GRID = "rgba(255,255,255,0.06)"

st.set_page_config(page_title="Garmin Solar", layout="wide")

# --- CSS for a cohesive green look ---
st.markdown(
    """
    <style>
    .stApp { background: radial-gradient(circle at 20% 0%, #0a1a07 0%, #0E1117 45%); }
    [data-testid="stMetricValue"] { color: #4cc406; font-weight: 700; }
    [data-testid="stMetricLabel"] { color: #C9C9C9; }
    h1, h2, h3 { color: #4cc406 !important; }
    .stMetric { background: rgba(76,196,6,0.05); border: 1px solid rgba(76,196,6,0.15);
                border-radius: 14px; padding: 14px 18px; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=60)
def load_data():
    if not os.path.exists(DB_PATH):
        return pd.DataFrame()
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT day, avg_intensity, max_intensity, sample_count "
        "FROM solar_intensity_daily ORDER BY day",
        conn,
    )
    conn.close()
    if df.empty:
        return df
    df["day"] = pd.to_datetime(df["day"])
    df["weekday"] = df["day"].dt.day_name()
    return df


def run_refresh(start, end):
    """Run the download pipeline (requires GARMIN_EMAIL/PASSWORD)."""
    script = os.path.join(os.path.dirname(__file__), "garmin_solar_to_sqlite.py")
    return subprocess.run(
        [sys.executable, script, start, end],
        capture_output=True, text=True,
    )


# ===================== HEADER =====================
st.title("Garmin Solar Dashboard")
st.caption("Daily solar intensity · Fenix 6X Pro Solar")

# ===================== SIDEBAR =====================
with st.sidebar:
    st.header("Controls")

    df_all = load_data()
    if df_all.empty:
        st.error("No data in SQLite. Run the pipeline first.")
        st.stop()

    min_d, max_d = df_all["day"].min().date(), df_all["day"].max().date()
    rng = st.date_input("Date range", value=(min_d, max_d), min_value=min_d, max_value=max_d)

    st.divider()
    st.subheader("Refresh data")
    c1, c2 = st.columns(2)
    rs = c1.text_input("From", value=str(min_d))
    re_ = c2.text_input("To", value=str(max_d))
    if st.button("Download from Garmin", use_container_width=True):
        if not os.environ.get("GARMIN_EMAIL"):
            st.warning("Set GARMIN_EMAIL / GARMIN_PASSWORD first (setx).")
        else:
            with st.spinner("Downloading from Garmin Connect..."):
                out = run_refresh(rs, re_)
            st.code((out.stdout or "")[-1500:] + (out.stderr or "")[-500:])
            st.cache_data.clear()
            st.rerun()

# Filter by selected range
if isinstance(rng, tuple) and len(rng) == 2:
    start, end = rng
    df = df_all[(df_all["day"].dt.date >= start) & (df_all["day"].dt.date <= end)].copy()
else:
    df = df_all.copy()

if df.empty:
    st.warning("No rows in the selected range.")
    st.stop()

# ===================== KPI =====================
best = df.loc[df["avg_intensity"].idxmax()]
peak = df.loc[df["max_intensity"].idxmax()]

k1, k2, k3, k4 = st.columns(4)
k1.metric("Average solar", f"{df['avg_intensity'].mean():.1f}%")
k2.metric("Peak maximum", f"{df['max_intensity'].max():.0f}%",
          help=f"on {peak['day'].date()}")
k3.metric("Sunniest day", best["day"].strftime("%d %b"),
          delta=f"{best['avg_intensity']:.1f}% avg")
k4.metric("Days with data", f"{len(df)}")

st.divider()

# ===================== MAIN CHART =====================
st.subheader("Daily trend")

fig = go.Figure()
# Max band (shaded area)
fig.add_trace(go.Scatter(
    x=df["day"], y=df["max_intensity"], name="Daily max",
    mode="lines", line=dict(color=GREEN_MID, width=1),
    fill="tozeroy", fillcolor="rgba(47,163,10,0.12)",
))
# Average line
fig.add_trace(go.Scatter(
    x=df["day"], y=df["avg_intensity"], name="Daily average",
    mode="lines+markers", line=dict(color=GREEN_BRIGHT, width=3),
    marker=dict(size=7, color=GREEN_DEEP, line=dict(color=GREEN_BRIGHT, width=1)),
))
fig.update_layout(
    template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    height=420, margin=dict(l=10, r=10, t=30, b=10),
    legend=dict(orientation="h", y=1.12, x=0),
    yaxis=dict(title="Intensity (%)", gridcolor=GRID, range=[0, 105]),
    xaxis=dict(gridcolor=GRID),
    hovermode="x unified",
)
st.plotly_chart(fig, use_container_width=True)

# ===================== ROW 2: BARS + WEEKDAY =====================
col_a, col_b = st.columns([2, 1])

with col_a:
    st.subheader("Average per day")
    bar = go.Figure(go.Bar(
        x=df["day"], y=df["avg_intensity"],
        marker=dict(
            color=df["avg_intensity"],
            colorscale=[[0, "#0f2e06"], [0.5, GREEN_MID], [1, GREEN_BRIGHT]],
            showscale=False,
        ),
        hovertemplate="%{x|%d %b}<br>%{y:.1f}%<extra></extra>",
    ))
    bar.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=320, margin=dict(l=10, r=10, t=10, b=10),
        yaxis=dict(title="%", gridcolor=GRID), xaxis=dict(gridcolor=GRID),
    )
    st.plotly_chart(bar, use_container_width=True)

with col_b:
    st.subheader("By weekday")
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    wk = df.groupby("weekday")["avg_intensity"].mean().reindex(order)
    wkfig = go.Figure(go.Bar(
        x=wk.values, y=labels, orientation="h",
        marker=dict(color=wk.values,
                    colorscale=[[0, "#0f2e06"], [1, GREEN_BRIGHT]], showscale=False),
        hovertemplate="%{y}: %{x:.1f}%<extra></extra>",
    ))
    wkfig.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=320, margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(title="%", gridcolor=GRID), yaxis=dict(autorange="reversed"),
    )
    st.plotly_chart(wkfig, use_container_width=True)

# ===================== TABLE =====================
with st.expander("View raw data"):
    show = df[["day", "avg_intensity", "max_intensity", "sample_count"]].copy()
    show["day"] = show["day"].dt.strftime("%Y-%m-%d")
    show.columns = ["Day", "Average %", "Max %", "Samples"]
    st.dataframe(show, use_container_width=True, hide_index=True)

st.caption("Source: Garmin Connect → SQLite · Streamlit dashboard")
