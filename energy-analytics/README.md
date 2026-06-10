# Energy Consumption Analytics

A small Streamlit dashboard over household energy-consumption data
(stored in `energy.db`, table `energy_consumption`).

## Contents
- `analysis.py` — data access (`get_energy`) and analytics helpers
  (`max_consumption`, `min_consumption`). Run directly to print a quick report.
- `app.py` — Streamlit dashboard (KPIs + green charts) that reuses the
  functions from `analysis.py`.
- `energy.db` — SQLite database with the `energy_consumption` table (20 rows).

## Run

```bash
pip install -r ../requirements.txt
streamlit run app.py
```

Or print the analysis to the console:

```bash
python analysis.py
```

## Dashboard
- KPIs: total kWh, total cost, top consumer, lowest consumer
- Total consumption per device
- Max and mean consumption per device type
- Consumption over time
- Cost per location

> Note: negative `consumption_kwh` values represent energy *produced*
> (e.g. a solar inverter), so `min_consumption` ignores them and reports the
> lowest real consumer.
