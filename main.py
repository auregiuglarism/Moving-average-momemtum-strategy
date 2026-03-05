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


if __name__ == "__main__":
    # --- Step 1: Apply binary gate to filter stock universe ---
    data_folder = 'Data/Assets'
    sp500_csv_path = 'data/sp500.csv'
    stock_universe, asset_data_dict = filter_stock_universe(data_folder, sp500_csv_path, rebalancing='weekly')

    # --- Step 2: Compute scoring for the filtered stock universe ---
    asset_data_list = [asset_data_dict[ticker] for ticker in stock_universe]
    sp500_data = pd.read_csv(sp500_csv_path, parse_dates=['Date'], index_col='Date')
    sp500_data = sp500_data.sort_index()
    scored_assets = compute_scoring(asset_data_list, sp500_data, advanced=True)

    # Now scored_assets contains the final composite scores for each asset that passed the binary gate
    # --- Step 3: We can compute portfolios ---


