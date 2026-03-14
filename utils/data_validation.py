"""
Data validation and cleaning utilities
"""
import pandas as pd
import os


def validate_asset_data(asset_df, ticker, max_daily_move=0.3, max_monthly_return=0.5):
    """
    Validate asset data for quality issues.

    Parameters
    ----------
    asset_df : pd.DataFrame
        Asset dataframe with 'price' column
    ticker : str
        Stock ticker symbol
    max_daily_move : float
        Max allowed daily return (e.g., 0.3 = 30%)
    max_monthly_return : float
        Max allowed monthly return (e.g., 0.5 = 50%)

    Returns
    -------
    bool
        True if data passes validation, False if corrupted
    """
    if len(asset_df) < 100:
        return False  # Too little data

    daily_return = asset_df['price'].pct_change()

    # Check for unrealistic daily moves (likely data errors or bankruptcies)
    extreme_daily = daily_return[abs(daily_return) > max_daily_move]
    if len(extreme_daily) > 5:  # Allow a few, but not many
        return False

    # Check for unrealistic monthly returns
    prices_monthly = asset_df['price'].resample('ME').last()
    monthly_return = prices_monthly.pct_change()
    extreme_monthly = monthly_return[abs(monthly_return) > max_monthly_return]
    if len(extreme_monthly) > 2:  # Allow one or two, but not many
        return False

    return True


def filter_clean_universe(data_folder, max_daily_move=0.3, max_monthly_return=0.5):
    """
    Filter stock universe to remove corrupted/delisted stocks.

    Parameters
    ----------
    data_folder : str
        Path to assets folder
    max_daily_move : float
        Max allowed daily return
    max_monthly_return : float
        Max allowed monthly return

    Returns
    -------
    list
        List of clean ticker symbols
    """
    clean_tickers = []
    removed_tickers = []

    for filename in os.listdir(data_folder):
        if filename.endswith('.csv'):
            ticker = filename.replace('yfinance_', '').replace('.csv', '')
            try:
                asset_df = pd.read_csv(
                    os.path.join(data_folder, filename),
                )
                asset_df = asset_df.iloc[2:]
                asset_df.rename(columns={"Price": "Date"}, inplace=True)
                asset_df["Date"] = pd.to_datetime(asset_df["Date"])
                asset_df.set_index("Date", inplace=True)
                asset_df = asset_df.astype(float)
                asset_df = asset_df.sort_index()

                if validate_asset_data(asset_df, ticker, max_daily_move, max_monthly_return):
                    clean_tickers.append(ticker)
                else:
                    removed_tickers.append(ticker)

            except Exception as e:
                removed_tickers.append(ticker)

    print(f"Data validation complete:")
    print(f"  Clean tickers: {len(clean_tickers)}")
    print(f"  Removed (corrupted): {len(removed_tickers)}")

    if len(removed_tickers) > 0:
        print(f"\n  Removed: {sorted(removed_tickers)[:10]}{'...' if len(removed_tickers) > 10 else ''}")

    return clean_tickers, removed_tickers


def clean_asset_returns(asset_df, max_daily_move=0.3, max_monthly_return=0.5):
    """
    Winsorize (cap) extreme returns in a single asset.

    Parameters
    ----------
    asset_df : pd.DataFrame
        Asset dataframe
    max_daily_move : float
        Maximum allowed daily return
    max_monthly_return : float
        Maximum allowed monthly return

    Returns
    -------
    pd.DataFrame
        Asset dataframe with capped returns
    """
    # Cap daily moves
    daily_return = asset_df['price'].pct_change()
    asset_df['price'] = asset_df['price'].copy()

    # Clip extreme daily changes by reconstructing prices
    mask = abs(daily_return) > max_daily_move
    if mask.any():
        capped_return = daily_return.clip(-max_daily_move, max_daily_move)
        # Reconstruct prices from capped returns
        asset_df.loc[mask, 'price'] = asset_df.loc[mask.shift(1), 'price'].values * (1 + capped_return[mask].values)

    return asset_df
