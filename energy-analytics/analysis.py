import os
import sqlite3
import pandas as pd

# Relative path so it works from anywhere (local, GitHub, Streamlit Cloud)
db_path = os.path.join(os.path.dirname(__file__), "energy.db")


def get_energy(db_path, query):
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


# === MAX CONSUMPTION (single device) ===
# idxmax() -> index of the row with the highest consumption in the whole table
# df.loc[...] -> pulls that row, then we take only the device name
def max_consumption(df):
    row = df.loc[df['consumption_kwh'].idxmax()]
    return row['device']


# === MIN CONSUMPTION (real consumers only) ===
# Exclude negative values (e.g. Solar Inverter produces energy, doesn't consume).
# Then idxmin() -> row with the lowest positive consumption -> device name.
def min_consumption(df):
    consumers = df[df['consumption_kwh'] > 0]
    row = consumers.loc[consumers['consumption_kwh'].idxmin()]
    return row['device']


# === CONSUMPTION PER HOUR (power rate) ===
# kWh / hours = the real power draw, not just the total consumed.
# A device can have a high total only because it runs many hours (e.g. a fridge);
# this shows how hard it pulls *per hour*. Returns one row per device, sorted desc.
# Only real consumers (positive kWh, duration > 0) are considered.
def consumption_per_hour(df):
    consumers = df[(df['consumption_kwh'] > 0) & (df['duration_hours'] > 0)].copy()
    consumers['kwh_per_hour'] = consumers['consumption_kwh'] / consumers['duration_hours']
    result = (consumers.groupby('device')['kwh_per_hour'].mean()
              .sort_values(ascending=False).reset_index())
    return result


# === PRODUCTION vs CONSUMPTION BALANCE ===
# Negative kWh = energy produced (e.g. solar inverter); positive = consumed.
# Returns total produced, total consumed and the net balance.
# net < 0  -> we consume more than we produce (we still buy from the grid)
# net > 0  -> we produce a surplus.
def production_consumption_balance(df):
    produced = -df[df['consumption_kwh'] < 0]['consumption_kwh'].sum()  # as a positive number
    consumed = df[df['consumption_kwh'] > 0]['consumption_kwh'].sum()
    net = produced - consumed
    return pd.Series({
        'produced_kwh': round(produced, 2),
        'consumed_kwh': round(consumed, 2),
        'net_kwh': round(net, 2),
    })


if __name__ == "__main__":
    energy_df = get_energy(db_path, "SELECT * FROM energy_consumption")

    print(energy_df.head())

    # Filter: only Appliance rows
    appliance = energy_df[energy_df['device_type'] == 'Appliance']
    print(appliance.head())

    # Max consumption per category (groupby)
    max_per_cat = energy_df.groupby('device_type')['consumption_kwh'].max().reset_index()
    print(max_per_cat)

    print("Top consumer:", max_consumption(energy_df))

    # Pivot table - mean consumption per device_type
    pivot = energy_df.pivot_table(values='consumption_kwh', index='device_type', aggfunc='mean')
    print(pivot)

    print("Lowest consumer:", min_consumption(energy_df))

    # Consumption per hour (power rate) per device
    print("\nConsumption per hour (kWh/h):")
    print(consumption_per_hour(energy_df))

    # Production vs consumption balance
    print("\nProduction / consumption balance:")
    print(production_consumption_balance(energy_df))
