# Solar Grid — Analiză energetică

Analiză a producției solare vs consum pe rețeaua electrică a României (6 zone, date orare/lunare 2024), cu un dashboard interactiv Streamlit.

Datele provin dint-un pipeline Databricks (layer **Gold**) și sunt trase local în SQLite pentru analiză offline.

## Structură

| Fișier | Rol |
|---|---|
| `gold_to_sqlite.py` | Extrage cele 4 tabele Gold din Azure Databricks → `solar_grid.db` local |
| `simulation.py` | Motorul de metrici — clase pe secțiuni (deficit/surplus, indici, mismatch, profil orar) |
| `dashboard.py` | Dashboard Streamlit peste metricile din `simulation.py` |

## Secțiuni de analiză

1. **Deficit / Surplus energetic** (anual, pe zonă) — grad de acoperire, indice de dependență, self-sufficiency ratio, volatilitate
2. **Indici lunari** — consum / producție / performanță (acoperire) + mismatch sezonier
3. **Mismatch sezonier** — dezalinierea producție vs consum, cine conduce decalajul, heatmap lună × zonă
4. **Profil intraday (orar)** — producție vs consum pe ore, cele două vârfuri de consum vs vârful de producție

## Rulare

```bash
pip install -r requirements.txt

# 1. Setează tokenul Databricks (NU e în cod)
#    PowerShell:  $env:DATABRICKS_TOKEN = "dapi..."
#    bash:        export DATABRICKS_TOKEN="dapi..."

# 2. Trage datele Gold în SQLite local
python gold_to_sqlite.py

# 3. Pornește dashboard-ul
streamlit run dashboard.py
```

## Concluzii cheie

- Toate zonele sunt în **deficit anual** de producție solară; Oltenia/Muntenia cele mai autonome (~87-90% acoperire), Transilvania cea mai dependentă (23%).
- **Producția conduce** dezalinierea: variază sezonier de ~5.5× mai mult decât consumul (care e aproape constant).
- **Mismatch sezonier**: supraproducție vara (iunie), deficit iarna (decembrie), echilibru toamna (septembrie).
- **Intraday**: consumul are două vârfuri (dimineața 7-9, seara 18-19) fix când soarele e slab; chiar la prânz acoperirea nu trece de ~45% — argumentul tehnic pentru stocare/baterii.

> Notă: tabelul de date conține doar producția **solară** — deficitul față de consum e acoperit de alte surse (hidro, nuclear, gaz) din mixul energetic, nu reflectat aici.
