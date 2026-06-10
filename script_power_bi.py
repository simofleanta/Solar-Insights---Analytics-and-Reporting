import sqlite3
import pandas as pd

# path absolut catre baza reala Garmin
db_path = r"C:\Power BI Projects\PY Files\garmin-solar\garmin_solar.sqlite"


def get_data_from_db(db_path, query):
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


# Power BI ia DataFrame-urile din scope -> functia TREBUIE apelata
solar_daily = get_data_from_db(db_path, "SELECT * FROM solar_intensity_daily ORDER BY day")

# verificare locala (Power BI ignora print-urile)
if __name__ == "__main__":
    print(solar_daily.shape)
    print(solar_daily.head())
