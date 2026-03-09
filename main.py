"""
Applies binary gate depending on the rebalancing frequency (weekly or monthly) 
and then computes the scoring for the assets that pass the gate.

Inside this filtered stock universe after scoring, we can compute the 3 different portfolios
pf_long - one long (buy & hold top 30 stocks according to scoring method)
pf_long_short - one long-short (buy & hold top 30, short bottom 30)
pf_mimicking - one factor mimicking(purely factor driven to evaluate our strategy) (buy and hold 50%, short 50%)
"""

import pandas as pd

from scoring import compute_scoring
from binary_gate import filter_stock_universe
from portfolios import compute_portfolios_timeframe


if __name__ == "__main__":
    # --- Step 1: Apply binary gate to filter stock universe ---
    data_folder = 'Data/Assets'
    sp500_csv_path = 'Data/S&P 500 Historical Data.csv'
    stock_universe, asset_data_dict = filter_stock_universe(data_folder, sp500_csv_path, rebalancing='weekly')

    # --- Step 2: Compute scoring for the filtered stock universe ---
    asset_data_list = [asset_data_dict[ticker] for ticker in stock_universe]
    sp500_data = pd.read_csv(sp500_csv_path, parse_dates=['Date'], index_col='Date')
    
    scored_assets = compute_scoring(asset_data_list, sp500_data, advanced=True)
    print("Scoring completed for assets that passed the binary gate.")

    # Now scored_assets contains the final composite scores for each asset that passed the binary gate
    # --- Step 3: We can compute portfolios ---
    pf_long, pf_long_short, pf_mimicking = compute_portfolios_timeframe(scored_assets, top_n=30, timeframe='2009-01-01', rebalancing=15)
    print(f"portfolio pf_long has {len(pf_long)} assets.")
    print(f"portfolio pf_long_short has {len(pf_long_short['long'])} long assets and {len(pf_long_short['short'])} short assets.")
    print(f"portfolio pf_mimicking has {len(pf_mimicking['long'])} long assets and {len(pf_mimicking['short'])} short assets.")

