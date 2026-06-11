"""Copiaza cele 4 tabele Gold (solar grid) din Azure Databricks intr-un SQLite local.
Pornesti warehouse-ul o singura data (prima query il trezeste ~30-60s), tragi datele
si dupa aia le explorezi local oricand, fara sa arzi credit Azure.
"""
import os
import sqlite3
from pathlib import Path

from databricks import sql

# --- Conexiune Azure Databricks (catalog databricks_solar_grid) ---
# Tokenul se citeste din variabila de mediu, NU se scrie in cod:
#   PowerShell:  $env:DATABRICKS_TOKEN = "dapi..."
#   bash:        export DATABRICKS_TOKEN="dapi..."
DATABRICKS_HOST = os.environ.get("DATABRICKS_HOST", "adb-7405610231425837.17.azuredatabricks.net")
DATABRICKS_HTTP_PATH = os.environ.get("DATABRICKS_HTTP_PATH", "/sql/1.0/warehouses/cc523686968f1a9f")
DATABRICKS_TOKEN = os.environ["DATABRICKS_TOKEN"]  # obligatoriu din mediu

SQLITE_PATH = str(Path(__file__).with_name("solar_grid.db"))

CATALOG = "databricks_solar_grid"
SCHEMA = "gold"  # daca da eroare, schimba in "default"
TABLES = [
    "gold_generation_vs_consumption",
    "gold_top_farms",
    "gold_surplus_deficit_zona",
    "gold_anomalii_grid",
]

# Mapare tip Databricks -> tip SQLite (afinitate)
def sqlite_type(dbx_type: str) -> str:
    t = dbx_type.lower()
    if any(x in t for x in ("int", "long", "short", "byte")):
        return "INTEGER"
    if any(x in t for x in ("double", "float", "decimal", "numeric")):
        return "REAL"
    if "boolean" in t:
        return "INTEGER"
    return "TEXT"  # string, date, timestamp etc. -> text


def extract(cursor, table):
    cursor.execute(f"SELECT * FROM {CATALOG}.{SCHEMA}.{table}")
    rows = cursor.fetchall()
    columns = [(c[0], c[1]) for c in cursor.description]  # (nume, tip)
    return columns, rows


def load(conn, table, columns, rows):
    cur = conn.cursor()
    cur.execute(f"DROP TABLE IF EXISTS {table}")
    cols_ddl = ", ".join(f'"{name}" {sqlite_type(typ)}' for name, typ in columns)
    cur.execute(f"CREATE TABLE {table} ({cols_ddl})")
    placeholders = ",".join("?" for _ in columns)
    # normalizeaza valori non-primitive (date/decimal) la str
    norm = [
        tuple(v if v is None or isinstance(v, (int, float, str)) else str(v) for v in r)
        for r in rows
    ]
    cur.executemany(f"INSERT INTO {table} VALUES ({placeholders})", norm)
    conn.commit()
    print(f"{table}: {len(rows)} randuri, {len(columns)} coloane")


if __name__ == "__main__":
    with sql.connect(
        server_hostname=DATABRICKS_HOST,
        http_path=DATABRICKS_HTTP_PATH,
        access_token=DATABRICKS_TOKEN,
    ) as db_conn:
        with db_conn.cursor() as cursor:
            sqlite_conn = sqlite3.connect(SQLITE_PATH)
            for table in TABLES:
                columns, rows = extract(cursor, table)
                load(sqlite_conn, table, columns, rows)
            sqlite_conn.close()

    print(f"\nGata - cele 4 tabele Gold sunt in {SQLITE_PATH}")
