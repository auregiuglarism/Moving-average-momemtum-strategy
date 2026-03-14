import pandas as pd
import requests
from io import StringIO

url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
headers = {"User-Agent": "Mozilla/5.0"}

response = requests.get(url, headers=headers)
html = StringIO(response.text)

df = pd.read_html(html)[0]

tickers = df["Symbol"].str.replace(".", "-", regex=False)

# Uncomment the line to save the tickers to a csv file
# tickers.to_csv("sp500_tickers.csv", index=False)

print(f"{len(tickers)} tickers saved.")

