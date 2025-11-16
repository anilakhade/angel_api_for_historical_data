# Angel One Historical Data Fetcher & Scanners

A Python script to fetch historical daily candle data for NSE equity stocks (filtered from NFO futures) using the **Angel One SmartAPI**, build a pivot table of the latest 10 trading days, and generate **continuous increase/decrease scanners** for 3, 4, and 5-day trends.

Perfect for building **daily stock screeners** and **momentum scanners**.

---

## Features

- Secure login with **TOTP (2FA)**
- Fetches **last ~60 trading days** of OHLCV data
- Filters stocks: NSE equities with active **FUTSTK** in NFO (excludes `TEST`)
- Builds **pivot table** (`latest_10_days.csv`) with closing prices
- Generates **6 scanner CSVs**:
  - `continuous_increase_3_days.csv`
  - `continuous_decrease_3_days.csv`
  - ... up to 5 days
- Rate-limit safe: **2 requests/sec** (under 3/sec API limit)
- Clean, modular, and ready for automation

---

## Output Files

| File | Description |
|------|-------------|
| `latest_10_days.csv` | Pivot: Symbol × Date (last 10 trading days), Close prices |
| `continuous_increase_X_days.csv` | Stocks with **strictly increasing** closes over X days |
| `continuous_decrease_X_days.csv` | Stocks with **strictly decreasing** closes over X days |

---

## Requirements

- Python 3.9+
- Angel One account + API key
- TOTP enabled (Google Authenticator)
