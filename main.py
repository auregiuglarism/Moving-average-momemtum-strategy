"""
Applies binary gate depending on the rebalancing frequency (weekly or monthly) 
and then computes the scoring for the assets that pass the gate.

Inside this filtered stock universe after scoring, we can compute the 3 different portfolios
pf_long - one long (buy & hold top 30 stocks according to scoring method)
pf_long_short - one long-short (buy & hold top 30, short bottom 30)
pf_mimicking - one factor mimicking(purely factor driven to evaluate our strategy) (buy and hold 50%, short 50%)
"""

import pandas as pd
import matplotlib.pyplot as plt

from scoring import compute_scoring
from binary_gate import filter_stock_universe, prep_stock_universe
from portfolios import compute_portfolios_timeframe


if __name__ == "__main__":
    # --- Step 0: Declaration ---
    data_folder = 'Data/tests' 
    sp500_csv_path = 'Data/S&P 500 Historical Data.csv'
    sp500_data = pd.read_csv(sp500_csv_path, parse_dates=['Date'], index_col='Date')
    sp500_data['Change %'] = (
        sp500_data['Change %']
        .str.replace('%', '', regex=False)
        .astype(float) / 100
    )
    sp500_df = sp500_data.sort_index()

    portfolio_long_value = 1.0
    portfolio_ls_value = 1.0
    portfolio_mim_value = 1.0
    portfolio_values = []  # will store dicts with date + 3 values

    dates = pd.date_range(
        start="2009-01-01",
        end="2026-01-01",
        freq="15D"   # rebalance every 15 days
    )

    rebalancing_filter = 'weekly' # or 'monthly'
    rebalancing_portfolios = 15 # or 30 for monthly

    binary_gate = False
    # Only apply scoring once since no binary gate
    if binary_gate == False:
        stock_universe, asset_data_dict = prep_stock_universe(data_folder)
        asset_data_list = [asset_data_dict[ticker] for ticker in stock_universe]
        scored_assets = compute_scoring(asset_data_list, sp500_df, advanced=True)
    
    for i in range(len(dates)-1):
        start = dates[i]
        end = dates[i+1]

        print("Timeframe:", start.strftime("%Y-%m-%d"))

        # --- Step 1: Apply binary gate to filter stock universe ---
        if binary_gate:
            stock_universe, asset_data_dict = filter_stock_universe(data_folder, sp500_csv_path, rebalancing=rebalancing_filter, timeframe=start)     
            # --- Step 2: Compute scoring for the filtered stock universe ---
            asset_data_list = [asset_data_dict[ticker] for ticker in stock_universe]
            scored_assets = compute_scoring(asset_data_list, sp500_df, advanced=True)

        # --- Step 3: We can compute portfolios and their returns ---
        pf_long, pf_long_short, pf_mimicking, r_long, r_ls, r_mim = compute_portfolios_timeframe(
            scored_assets,
            top_n=30,
            timeframe=start,
            rebalancing=rebalancing_portfolios,
            equal_weights=True
        )

        portfolio_values.append({
            "date": end,
            "pf_long": portfolio_long_value,
            "pf_long_short": portfolio_ls_value,
            "pf_mimicking": portfolio_mim_value
        })

# --- Plot Portfolio Performance ---
# Convert to DataFrame
perf_df = pd.DataFrame(portfolio_values)
perf_df.set_index("date", inplace=True)

# Convert periodic returns to cumulative growth of $1
cumulative_df = (1 + perf_df).cumprod()

# Print final total returns
print(f"1$ with pf_long has return: {cumulative_df['pf_long'].iloc[-1]-1:.2%}")
print(f"1$ with pf_long_short has return: {cumulative_df['pf_long_short'].iloc[-1]-1:.2%}")
print(f"1$ with factor mimicking has return: {cumulative_df['pf_mimicking'].iloc[-1]-1:.2%}")

# Resample to the same frequency as your portfolio rebalancing
# sp500_resampled = sp500_df['Change %'].resample('15D').sum()  # sum of returns over 15D
# sp500_cumulative = (1 + sp500_resampled).cumprod()
# sp500_cumulative = sp500_cumulative.loc[cumulative_df.index]  # align with portfolio dates

# Plot all three portfolios on the same graph + S&P 500 for comparison
plt.figure(figsize=(12,6))
plt.plot(cumulative_df.index, cumulative_df['pf_long'], label='Long Top 30')
plt.plot(cumulative_df.index, cumulative_df['pf_long_short'], label='Long-Short Top/Bottom 30')
plt.plot(cumulative_df.index, cumulative_df['pf_mimicking'], label='Factor Mimicking')
# plt.plot(sp500_cumulative.index, sp500_cumulative.values, label='S&P 500', linestyle='--', color='black')
plt.title("Growth of $1 Invested in Each Portfolio")
plt.xlabel("Date")
plt.ylabel("Portfolio Value ($)")
plt.legend()
plt.grid(True)
plt.show()



    

