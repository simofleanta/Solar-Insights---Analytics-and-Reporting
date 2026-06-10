"""
Garmin Fenix 6X Pro Solar -> SQLite
Downloads daily solar intensity from Garmin Connect and stores it in SQLite.

Run:
    setx GARMIN_EMAIL "your_email"       (once)
    setx GARMIN_PASSWORD "your_password" (once)
    python garmin_solar_to_sqlite.py             -> last 30 days
    python garmin_solar_to_sqlite.py 2026-05-01 2026-06-09

Idempotent: run as often as you like, rows are not duplicated (INSERT OR REPLACE per day).
"""

import os
import sys
import sqlite3
from datetime import date, timedelta

from garminconnect import Garmin

DB_PATH = os.path.join(os.path.dirname(__file__), "garmin_solar.sqlite")


def get_dates():
    """Date range from CLI args, or the last 30 days by default."""
    if len(sys.argv) >= 3:
        start = date.fromisoformat(sys.argv[1])
        end = date.fromisoformat(sys.argv[2])
    else:
        end = date.today()
        start = end - timedelta(days=30)
    return start, end


def init_db(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS solar_intensity_daily (
            day            TEXT PRIMARY KEY,   -- YYYY-MM-DD
            avg_intensity  REAL,               -- daily average %
            max_intensity  REAL,               -- daily peak %
            sample_count   INTEGER,            -- number of intraday samples
            device_id      TEXT
        )
        """
    )
    # Intraday table (granular) - useful for an hourly chart in Power BI
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS solar_intensity_intraday (
            ts          TEXT PRIMARY KEY,   -- ISO timestamp
            day         TEXT,
            intensity   REAL,
            device_id   TEXT
        )
        """
    )
    conn.commit()


def find_solar_device(api):
    """Find the device with solar support."""
    devices = api.get_devices()
    for d in devices:
        name = (d.get("productDisplayName") or d.get("displayName") or "").lower()
        if "solar" in name:
            return str(d.get("deviceId")), name
    # Fallback: first device
    if devices:
        d = devices[0]
        return str(d.get("deviceId")), (d.get("productDisplayName") or "device")
    return None, None


def fetch_solar_for_day(api, device_id, day):
    """
    Return (avg, max, count, intraday_list[(ts, intensity)]) for a day.
    intraday_list may be empty if the API only returns an aggregate.
    """
    iso = day.isoformat()
    data = api.get_device_solar_data(device_id, iso)
    if not data:
        return None

    # Typical shape: data["deviceSolarInput"]["solarDailyDataDTOs"] or
    # variants with a list of samples. Handle several shapes defensively.
    samples = []

    def harvest(obj):
        """Recursively collect (time, intensity) pairs."""
        if isinstance(obj, dict):
            # Typical intraday sample
            if "solarUtilization" in obj or "solarIntensity" in obj:
                val = obj.get("solarUtilization", obj.get("solarIntensity"))
                ts = obj.get("startGmt") or obj.get("timestamp") or obj.get("startTimeGmt")
                if val is not None and str(val).strip() != "":
                    try:
                        samples.append((ts, float(val)))
                    except (TypeError, ValueError):
                        pass
            for v in obj.values():
                harvest(v)
        elif isinstance(obj, list):
            for v in obj:
                harvest(v)

    harvest(data)

    if not samples:
        return None

    vals = [v for _, v in samples]
    avg = sum(vals) / len(vals)
    mx = max(vals)
    intraday = [(ts, v) for ts, v in samples if ts]
    return avg, mx, len(vals), intraday


def main():
    email = os.environ.get("GARMIN_EMAIL")
    password = os.environ.get("GARMIN_PASSWORD")
    if not email or not password:
        sys.exit("Missing GARMIN_EMAIL / GARMIN_PASSWORD environment variables.")

    start, end = get_dates()
    print(f"Range: {start} -> {end}")

    api = Garmin(email, password)
    api.login()  # if you have 2FA, it will prompt for the code in the console (via garth)
    print("Login OK")

    device_id, dev_name = find_solar_device(api)
    print(f"Device: {dev_name} (id={device_id})")

    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    day = start
    total = 0
    while day <= end:
        try:
            res = fetch_solar_for_day(api, device_id, day)
        except Exception as e:
            print(f"  {day}: error ({e})")
            res = None

        if res:
            avg, mx, cnt, intraday = res
            conn.execute(
                "INSERT OR REPLACE INTO solar_intensity_daily "
                "(day, avg_intensity, max_intensity, sample_count, device_id) "
                "VALUES (?,?,?,?,?)",
                (day.isoformat(), round(avg, 2), round(mx, 2), cnt, device_id),
            )
            for ts, val in intraday:
                conn.execute(
                    "INSERT OR REPLACE INTO solar_intensity_intraday "
                    "(ts, day, intensity, device_id) VALUES (?,?,?,?)",
                    (str(ts), day.isoformat(), round(val, 2), device_id),
                )
            print(f"  {day}: avg={avg:.1f}% max={mx:.1f}% ({cnt} samples)")
            total += 1
        else:
            print(f"  {day}: no solar data")

        day += timedelta(days=1)

    conn.commit()
    conn.close()
    print(f"\nDone. {total} days saved to {DB_PATH}")


if __name__ == "__main__":
    main()
