# Solar Insights — Analytics & Reporting

Pipeline de date și raportare pentru intensitatea solară captată de un ceas **Garmin Fenix 6X Pro Solar**.
Datele sunt descărcate din Garmin Connect, stocate în SQLite și vizualizate în Streamlit și Power BI.

## Componente

| Fișier | Rol |
|---|---|
| `garmin_solar_to_sqlite.py` | Descarcă intensitatea solară zilnică din Garmin Connect → SQLite (idempotent) |
| `app.py` | Dashboard Streamlit (trend zilnic, KPI-uri, medie pe zi din săptămână) |
| `script_power_bi.py` | Script pentru conectorul Python din Power BI (returnează `solar_daily`) |
| `requirements.txt` | Dependențe Python |

## Schema datelor (SQLite)

**`solar_intensity_daily`** — un rând pe zi:

| coloană | descriere |
|---|---|
| `day` | data (YYYY-MM-DD) |
| `avg_intensity` | media zilnică a intensității solare (%) |
| `max_intensity` | vârful zilnic (%) |
| `sample_count` | număr de citiri din zi (~1440 = zi completă) — indicator de încredere |
| `device_id` | id-ul ceasului |

## Utilizare

### 1. Configurare credențiale (o singură dată)
```powershell
setx GARMIN_EMAIL "email_garmin"
setx GARMIN_PASSWORD "parola_garmin"
```

### 2. Instalare dependențe
```powershell
pip install -r requirements.txt
```

### 3. Descărcare date
```powershell
python garmin_solar_to_sqlite.py                 # ultimele 30 de zile
python garmin_solar_to_sqlite.py 2026-05-01 2026-06-09   # interval specific
```

### 4. Dashboard Streamlit
```powershell
streamlit run app.py
```

### 5. Power BI
**Get Data → Python script** → lipești conținutul din `script_power_bi.py` → în Navigator bifezi `solar_daily` → **Load**.

## Note

- Baza de date (`*.sqlite`) conține date personale și **nu** este urcată în repo (vezi `.gitignore`).
- Credențialele Garmin se citesc din variabile de mediu, nu sunt stocate în cod.
