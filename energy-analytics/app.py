import pandas as pd
import plotly.express as px
import streamlit as st

# Reuse the functions FROM analysis.py (we don't rewrite them)
from analysis import db_path, get_energy, max_consumption, min_consumption

st.set_page_config(page_title="Energy Dashboard", layout="wide")

# Green palettes used across the dashboard
GREEN_SEQ = "Greens"
GREEN_LINE = "#2e7d32"


@st.cache_data
def load():
    df = get_energy(db_path, "SELECT * FROM energy_consumption")
    df['date'] = pd.to_datetime(df['date'])
    return df


energy_df = load()

# ---------------- Filters ----------------
st.sidebar.header("Filters")
types = st.sidebar.multiselect(
    "Device type", sorted(energy_df['device_type'].dropna().unique()),
    default=sorted(energy_df['device_type'].dropna().unique()))
locations = st.sidebar.multiselect(
    "Location", sorted(energy_df['location'].dropna().unique()),
    default=sorted(energy_df['location'].dropna().unique()))
dff = energy_df[energy_df['device_type'].isin(types) & energy_df['location'].isin(locations)]

st.title("Energy Consumption Dashboard")

if dff.empty:
    st.warning("No rows match the selected filters.")
    st.stop()

# ---------------- KPIs (max_consumption / min_consumption from analysis.py) ----------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total kWh", f"{dff['consumption_kwh'].sum():.1f}")
c2.metric("Total cost ($)", f"{dff['cost_usd'].sum():.2f}")
c3.metric("Top consumer", max_consumption(dff))
c4.metric("Lowest consumer", min_consumption(dff))

st.divider()

# ---------------- Total consumption per device ----------------
st.subheader("Total consumption per device")
by_device = (dff.groupby('device')['consumption_kwh'].sum()
             .sort_values(ascending=False).reset_index())
fig = px.bar(by_device.sort_values('consumption_kwh'),
             x='consumption_kwh', y='device', orientation='h',
             color='consumption_kwh', color_continuous_scale=GREEN_SEQ)
fig.update_layout(showlegend=False)
st.plotly_chart(fig, use_container_width=True)

# ---------------- Max per category + Mean per category ----------------
g1, g2 = st.columns(2)
with g1:
    st.subheader("Max consumption per category")
    max_cat = dff.groupby('device_type')['consumption_kwh'].max().reset_index()
    st.plotly_chart(
        px.bar(max_cat.sort_values('consumption_kwh'),
               x='consumption_kwh', y='device_type', orientation='h',
               color='consumption_kwh', color_continuous_scale=GREEN_SEQ),
        use_container_width=True)
with g2:
    st.subheader("Mean consumption per category")
    pivot = dff.pivot_table(values='consumption_kwh', index='device_type',
                            aggfunc='mean').reset_index()
    st.plotly_chart(
        px.bar(pivot.sort_values('consumption_kwh'),
               x='consumption_kwh', y='device_type', orientation='h',
               color='consumption_kwh', color_continuous_scale=GREEN_SEQ),
        use_container_width=True)

# ---------------- Consumption over time ----------------
st.subheader("Consumption over time")
by_date = dff.groupby('date')['consumption_kwh'].sum().reset_index()
fig_line = px.line(by_date, x='date', y='consumption_kwh', markers=True)
fig_line.update_traces(line_color=GREEN_LINE, marker_color=GREEN_LINE)
st.plotly_chart(fig_line, use_container_width=True)

# ---------------- Cost per location ----------------
st.subheader("Cost per location")
by_loc = dff.groupby('location')['cost_usd'].sum().reset_index()
st.plotly_chart(
    px.pie(by_loc, names='location', values='cost_usd', hole=0.4,
           color_discrete_sequence=px.colors.sequential.Greens[::-1]),
    use_container_width=True)
