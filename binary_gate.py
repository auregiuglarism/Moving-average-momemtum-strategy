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
def filter_stock_universe(data_folder, sp500_csv_path, rebalancing='monthly'):
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
    
    # Loop through asset CSVs
    for filename in os.listdir(data_folder):
        if filename.endswith('.csv'):
            ticker = filename.replace('.csv','')
            print(f"Processing {ticker}...")
            asset_path = os.path.join(data_folder, filename)
            asset_data = pd.read_csv(asset_path, parse_dates=['date'], index_col='date')
            asset_data = asset_data.sort_index()
            
            # --- Binary gate calculations ---
            asset_data_temp = asset_data.copy()  # make a temporary copy
            asset_data_temp['MA200'] = asset_data_temp['price'].rolling(window=200).mean() # 200 trading days
            
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
            
            # Latest values for binary condition
            latest_price = asset_data_temp['price'].iloc[-1]
            latest_ma200 = asset_data_temp['MA200'].iloc[-1]
            latest_rs = combined['RS'].iloc[-1]
            
            if (latest_price > latest_ma200) and (latest_rs > 0):
                stock_universe.append(ticker)
                # Keep the original asset_data (just date, price, volume)
                asset_data_dict[ticker] = asset_data.copy()
    
    return stock_universe, asset_data_dict


# Uncomment to test
if __name__ == "__main__":
    remove_empty_csv_files()  # Run this once to clean up empty files
    # data_folder = 'Data/Assets'
    # sp500_csv_path = 'Data/S&P 500 Historical Data.csv'
    # stock_universe, asset_data_dict = filter_stock_universe(data_folder, sp500_csv_path, rebalancing='weekly')
    # print("Stock universe after binary gate:", stock_universe)
