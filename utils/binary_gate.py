"""
Applies the binary gate condition in order to sort the data and 
only keep assets that satisfy the condition. Then we will compute the score in scoring.py.
"""

import pandas as pd
import os

# --- Remove empty CSV files before processing, only run once inside this file directly. ---
def remove_empty_csv_files(folder_path='Data/Assets'):
    """
    Deletes CSV files that contain headers but no data rows.

    Parameters
    ----------
    folder_path : str
        Path to folder containing CSV files
    """

    removed_files = 0

    for filename in os.listdir(folder_path):
        if filename.endswith(".csv"):
            file_path = os.path.join(folder_path, filename)

            try:
                df = pd.read_csv(file_path)

                # Check if dataframe has no rows
                if df.empty:
                    os.remove(file_path)
                    removed_files += 1
                    print(f"Deleted empty file: {filename}")

            except Exception as e:
                # If file cannot be read, remove it
                os.remove(file_path)
                removed_files += 1
                print(f"Deleted corrupted file: {filename}")

    print(f"\nTotal removed files: {removed_files}")

# --- Binary gate condition to save computation time ---
def filter_stock_universe(data_folder, sp500_csv_path, rebalancing='monthly', timeframe='2009-01-01'):
    """
    Filters assets that pass the binary gate condition:
        1. Price > 200-day moving average
        2. Relative strength > 0
    After passing the gate, returns the list of tickers
    and keeps the original asset DataFrames unmodified.
    
    Parameters:
        data_folder: folder with asset CSVs
        sp500_csv_path: S&P500 CSV file
        rebalancing: 'weekly' or 'monthly'
        
    Returns:
        stock_universe: list of tickers passing the gate
        asset_data_dict: dict of {ticker: original asset DataFrame}
    """
    
    stock_universe = []
    asset_data_dict = {}
    
    # Load S&P 500 data
    sp500 = pd.read_csv(sp500_csv_path, parse_dates=['Date'], index_col='Date')
    sp500['Change %'] = (
        sp500['Change %']
        .str.replace('%', '', regex=False)
        .astype(float) / 100
    )
    sp500 = sp500.sort_index()
    
    # Resample S&P500
    if rebalancing == 'weekly':
        sp500_resampled = sp500.resample('W').last()
    elif rebalancing == 'monthly':
        sp500_resampled = sp500.resample('M').last()
    else:
        raise ValueError("rebalancing must be 'weekly' or 'monthly'")
    
    target_date = pd.to_datetime(timeframe)
    # Loop through asset CSVs
    for filename in os.listdir(data_folder):
        if filename.endswith('.csv'):
            ticker = filename.replace('yfinance_', '').replace('.csv', '')
            print(f"Processing {ticker}...")
            asset_path = os.path.join(data_folder, filename)
            asset_data = pd.read_csv(asset_path)
            asset_data = asset_data.iloc[2:]
            asset_data.rename(columns={"Price": "Date"}, inplace=True)
            asset_data["Date"] = pd.to_datetime(asset_data["Date"])
            asset_data.set_index("Date", inplace=True)
            asset_data = asset_data.astype(float)
            asset_data_temp = asset_data.copy()
            asset_data_temp.sort_index()

            # --- Binary gate calculations ---
            asset_data_temp['MA200'] = asset_data_temp['price'].rolling(window=200).mean()

            # Resample for RS
            if rebalancing == 'weekly':
                asset_resampled = asset_data_temp.resample('W').last()
            else:
                asset_resampled = asset_data_temp.resample('M').last()

            asset_returns = asset_resampled['price'].pct_change()
            sp500_returns = sp500_resampled['Change %']

            combined = pd.DataFrame({
                'Asset_Return': asset_returns,
                'SP500_Return': sp500_returns
            }).dropna()

            combined['RS'] = combined['Asset_Return'] - combined['SP500_Return']

            # --- Find values at the rebalance date ---
            price_idx = asset_data_temp.index.get_indexer([target_date], method="nearest")[0]
            price_date = asset_data_temp.index[price_idx]

            rs_idx = combined.index.get_indexer([target_date], method="nearest")[0]
            rs_date = combined.index[rs_idx]

            price = asset_data_temp.iloc[price_idx]['price']
            ma200 = asset_data_temp.iloc[price_idx]['MA200']
            rs = combined.iloc[rs_idx]['RS']

            # optional tolerance
            if abs((price_date - target_date).days) > 7:
                continue

            # binary gate
            if (price > ma200) and (rs > 0):
                stock_universe.append(ticker)
                asset_data_dict[ticker] = asset_data.copy()
    
    return stock_universe, asset_data_dict

def prep_stock_universe(data_folder):
    stock_universe = []
    asset_data_dict = {}
    
    for filename in os.listdir(data_folder):
        if filename.endswith('.csv'):
            ticker = filename.replace('yfinance_', '').replace('.csv', '')
            print(f"Processing {ticker}...")
            stock_universe.append(ticker)

            asset_path = os.path.join(data_folder, filename)
            asset_data = pd.read_csv(asset_path)
            asset_data = asset_data.iloc[2:]
            asset_data.rename(columns={"Price": "Date"}, inplace=True)
            asset_data["Date"] = pd.to_datetime(asset_data["Date"])
            asset_data.set_index("Date", inplace=True)
            asset_data = asset_data.astype(float)
            asset_data_dict[ticker] = asset_data.copy()

    return stock_universe, asset_data_dict


# Uncomment to test
if __name__ == "__main__":
    pass
    # remove_empty_csv_files()  # Run this only once to clean up empty files
    # data_folder = 'Data/Assets'
    # sp500_csv_path = 'Data/S&P 500 Historical Data.csv'
    # stock_universe, asset_data_dict = filter_stock_universe(data_folder, sp500_csv_path, rebalancing='weekly', timeframe='2009-01-01')
    # print("Stock universe after binary gate:", stock_universe)
    # print ("Universe Size:", len(stock_universe), "stocks")
