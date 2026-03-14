import yfinance as yf
import pandas as pd
import time
import os

# Your ticker list
df = pd.read_csv("data/sp500_tickers.csv")
tickers = df["Symbol"].tolist()


# Create output folder
output_folder = "data/stocks"
os.makedirs(output_folder, exist_ok=True)

# Download settings
start_date = "2020-01-01"
end_date = None  # None = today

for ticker in tickers:
    try:
        print(f"Downloading {ticker}...")

        data = yf.download(
            ticker,
            start=start_date,
            end=end_date,
            progress=False
        )

        if not data.empty:
            filepath = f"{output_folder}/{ticker}.csv"
            data.to_csv(filepath)
            print(f"Saved: {filepath}")
        else:
            print(f"No data for {ticker}")

        time.sleep(1)  # avoid rate limiting

    except Exception as e:
        print(f"Error downloading {ticker}: {e}")

print("Download complete.")
