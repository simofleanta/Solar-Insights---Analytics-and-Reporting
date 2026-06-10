# Solar Insights — Analytics & Reporting

Data pipeline and reporting for solar intensity captured by a **Garmin Fenix 6X Pro Solar** watch.
Data is downloaded from Garmin Connect, stored in SQLite, and visualized in Streamlit and Power BI.

## Components

| File | Purpose |
|---|---|
| `garmin_solar_to_sqlite.py` | Downloads daily solar intensity from Garmin Connect → SQLite (idempotent) |
| `app.py` | Streamlit dashboard (daily trend, KPIs, average by weekday) |
| `script_power_bi.py` | Script for the Power BI Python connector (returns `solar_daily`) |
| `requirements.txt` | Python dependencies |

## Data schema (SQLite)

**`solar_intensity_daily`** — one row per day:

| Column | Description |
|---|---|
| `day` | Date (YYYY-MM-DD) |
| `avg_intensity` | Daily average solar intensity (%) |
| `max_intensity` | Daily peak (%) |
| `sample_count` | Number of readings in the day (~1440 = full day) — confidence indicator |
| `device_id` | Watch device id |

## Usage

### 1. Configure credentials (once)
```powershell
setx GARMIN_EMAIL "your_garmin_email"
setx GARMIN_PASSWORD "your_garmin_password"
```

### 2. Install dependencies
```powershell
pip install -r requirements.txt
```

### 3. Download data
```powershell
python garmin_solar_to_sqlite.py                         # last 30 days
python garmin_solar_to_sqlite.py 2026-05-01 2026-06-09   # specific range
```

### 4. Streamlit dashboard
```powershell
streamlit run app.py
```

### 5. Power BI
**Get Data → Python script** → paste the contents of `script_power_bi.py` → in the Navigator, check `solar_daily` → **Load**.

## Notes

- The database (`*.sqlite`) holds personal data and is **not** committed to the repo (see `.gitignore`).
- Garmin credentials are read from environment variables, never stored in code.
