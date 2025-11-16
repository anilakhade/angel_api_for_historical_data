# angel_api_for_historical_data.py

import time
import pandas as pd
from datetime import datetime, timedelta
from SmartApi.smartConnect import SmartConnect
import pyotp
from logzero import logger

# Import REAL requests (must be installed before smartapi-python)
import requests
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# ==== CONFIG ====
API_KEY = 'your_api_key'
CLIENT_CODE = 'your_client_code'
PASSWORD = 'your_password'
TOTP_SECRET = 'your_totp'

N_DAYS = 60
PIVOT_DAYS = 10
SLEEP_BETWEEN = 0.5
TIMEOUT = 30


# ==== LOGIN ====
def login():
    totp = pyotp.TOTP(TOTP_SECRET).now()
    smart_api = SmartConnect(api_key=API_KEY)

    # Use real Session to avoid SmartApi's fake requests
    session = Session()
    session.timeout = TIMEOUT
    retry = Retry(total=3, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)

    # Replace smart_api's session
    smart_api.reqsession = session

    try:
        smart_api.generateSession(CLIENT_CODE, PASSWORD, totp)
        print("Login successful!")
        return smart_api
    except Exception as e:
        print("Login failed:", e)
        raise


# === REST UNCHANGED ===
def get_filtered_stocks():
    url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
    df1 = pd.read_json(url)
    futstk = df1[(df1["instrumenttype"] == "FUTSTK") & (df1["exch_seg"] == "NFO")]
    unique_names = [n for n in futstk['name'].unique() if not n.endswith('TEST')]
    new_df = df1[
        (df1['exch_seg'] == 'NSE') &
        (df1['instrumenttype'] == '') &
        (df1['name'].isin(unique_names))
    ][['token', 'symbol']]
    print(f"Found {len(new_df)} stocks.")
    return new_df


def fetch_all_data(smart_api, new_df):
    end = datetime.now().strftime("%Y-%m-%d 15:30")
    start = (datetime.now() - timedelta(days=N_DAYS + 10)).strftime("%Y-%m-%d 09:15")
    all_data = []
    for _, row in new_df.iterrows():
        params = {
            "exchange": "NSE",
            "symboltoken": row['token'],
            "interval": "ONE_DAY",
            "fromdate": start,
            "todate": end
        }
        try:
            resp = smart_api.getCandleData(params)
            if resp.get('data'):
                df = pd.DataFrame(resp['data'], columns=["datetime", "open", "high", "low", "close", "volume"])
                df["datetime"] = pd.to_datetime(df["datetime"])
                df['symbol'] = row['symbol']
                all_data.append(df)
        except Exception as e:
            logger.error(f"Error {row['symbol']}: {e}")
        time.sleep(SLEEP_BETWEEN)
    df = pd.concat(all_data, ignore_index=True)
    df['date'] = df['datetime'].dt.date
    df = df.drop(columns=['datetime'])
    print(f"Fetched {len(df)} rows.")
    return df


def create_pivot(df):
    latest = df.groupby('symbol').tail(PIVOT_DAYS)
    pivot = latest.pivot(index='symbol', columns='date', values='close').reset_index()
    pivot.columns.name = None
    cols = sorted(pivot.columns[1:])[-PIVOT_DAYS:]
    pivot = pivot[['symbol'] + cols]
    pivot.to_csv(f'latest_{PIVOT_DAYS}_days.csv', index=False)
    return pivot


def scanner(pivot, days, direction):
    cols = pivot.columns[-days:]
    mask = (pivot[cols].apply(lambda r: r.is_monotonic_increasing, axis=1) if direction == "up"
            else pivot[cols].apply(lambda r: r.is_monotonic_decreasing, axis=1))
    name = "increase" if direction == "up" else "decrease"
    result = pivot.loc[mask, ['symbol'] + list(cols)]
    result.to_csv(f'continuous_{name}_{days}_days.csv', index=False)
    print(f"{len(result)} stocks {name} for {days} days")


if __name__ == "__main__":
    smart_api = login()
    stocks = get_filtered_stocks()
    data = fetch_all_data(smart_api, stocks)
    pivot = create_pivot(data)
    for d in [3, 4, 5]:
        scanner(pivot, d, "up")
        scanner(pivot, d, "down")
    print("All done.")
