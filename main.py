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

from utils.scoring import compute_scoring
from utils.binary_gate import filter_stock_universe, prep_stock_universe
from utils.portfolios import compute_portfolios_timeframe

from config import DEBUG_MAIN, DEBUG_MAIN_ABNORMAL, rebalancing_filter, rebalancing_portfolios, advanced_scoring, dates, binary_gate, equal_weights, start_value, smoothing

if __name__ == "__main__":
    # --- Step 0: Declaration ---
    data_folder = 'Data/tests' if DEBUG_MAIN else 'Data/Assets'
    sp500_csv_path = 'Data/S&P 500 Historical Data.csv'
    sp500_data = pd.read_csv(sp500_csv_path, parse_dates=['Date'], index_col='Date')
    sp500_data['Change %'] = (
        sp500_data['Change %']
        .str.replace('%', '', regex=False)
        .astype(float) / 100
    )
    sp500_df = sp500_data.sort_index()
    sp500df_copy = sp500_df.copy() # we need an unprocessed copy for later.

    portfolio_long_value = start_value
    portfolio_ls_value = start_value
    portfolio_mim_value = start_value
    portfolio_values = []  # will store dicts with date + 3 values

    # Only apply scoring once since no binary gate
    if binary_gate == False:
        stock_universe, asset_data_dict = prep_stock_universe(data_folder)
        print("Stock universe:", len(stock_universe)) 
        asset_data_list = [asset_data_dict[ticker] for ticker in stock_universe]
        scored_assets = compute_scoring(asset_data_list, sp500_df, advanced=advanced_scoring, smoothing=smoothing)
    
    for i in range(len(dates)-1):
        start = dates[i]
        end = dates[i+1]

        # --- Step 1: Apply binary gate to filter stock universe ---
        if binary_gate:
            stock_universe, asset_data_dict = filter_stock_universe(data_folder, sp500_csv_path, rebalancing=rebalancing_filter, timeframe=start)    
            print("Stock universe:", len(stock_universe))  
            # --- Step 2: Compute scoring for the filtered stock universe ---
            asset_data_list = [asset_data_dict[ticker] for ticker in stock_universe]
            scored_assets = compute_scoring(asset_data_list, sp500_df, advanced=advanced_scoring, smoothing=smoothing)

        # --- Step 3: We can compute portfolios and their returns ---
        pf_long, pf_long_short, pf_mimicking, r_long, r_ls, r_mim = compute_portfolios_timeframe(
            scored_assets,
            top_n=30,
            timeframe=start,
            rebalancing=rebalancing_portfolios,
            equal_weights=equal_weights
        )

        if pf_long is not None: # Else go to next timeframe, continue the loop
            print("Timeframe:", start.strftime("%Y-%m-%d"))
            if abs(r_long) > 1 and DEBUG_MAIN_ABNORMAL:
                print("WARNING abnormal return long:", r_long)
            if abs(r_ls) > 1 and DEBUG_MAIN_ABNORMAL:
                print("WARNING abnormal return long-short:", r_ls)
            if abs(r_mim) > 1 and DEBUG_MAIN_ABNORMAL:
                print("WARNING abnormal return mimicking:", r_mim)

            print(f"Average weekly return (top 30): {r_long:.2%}") if DEBUG_MAIN_ABNORMAL else None
            print(f"Average weekly return (long-short): {r_ls:.2%}") if DEBUG_MAIN_ABNORMAL else None
            print(f"Average weekly return (mimicking): {r_mim:.2%}") if DEBUG_MAIN_ABNORMAL else None

            portfolio_long_value *= (1 + r_long)
            portfolio_ls_value *= (1 + r_ls)
            portfolio_mim_value *= (1 + r_mim)

            print(f"Cumulative pf_long: {portfolio_long_value:.2f}x") if DEBUG_MAIN_ABNORMAL else None
            print(f"Cumulative pf_long_short: {portfolio_ls_value:.2f}x") if DEBUG_MAIN_ABNORMAL else None
            print(f"Cumulative pf_mimicking: {portfolio_mim_value:.2f}x") if DEBUG_MAIN_ABNORMAL else None

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

# Cumulative returns
cumulative_df = perf_df

# Compute S&P 500 returns exactly at the portfolio rebalance dates
sp500_cumulative_aligned = pd.Series(index=cumulative_df.index, dtype=float)
prev = sp500df_copy['Change %'].iloc[0]
sp500_cumulative_aligned.iloc[0] = 1.0

for i, date in enumerate(cumulative_df.index[1:], 1):
    start = cumulative_df.index[i-1]
    end = date
    returns = sp500df_copy.loc[start:end, 'Change %']
    sp500_cumulative_aligned.iloc[i] = sp500_cumulative_aligned.iloc[i-1] * (1 + returns).prod()

# Print final cumulative returns
print(f"1$ with pf_long has return: {cumulative_df['pf_long'].iloc[-1]-1:.2%}") 
print(f"1$ with pf_long_short has return: {cumulative_df['pf_long_short'].iloc[-1]-1:.2%}") 
print(f"1$ with factor mimicking has return: {cumulative_df['pf_mimicking'].iloc[-1]-1:.2%}") 
print(f"1$ with S&P 500 has return: {sp500_cumulative_aligned.iloc[-1]-1:.2%}")

# Annualized returns
n_periods = len(portfolio_values)
pf_long_end = cumulative_df['pf_long'].iloc[-1]
pf_ls_end = cumulative_df['pf_long_short'].iloc[-1]
pf_mim_end = cumulative_df['pf_mimicking'].iloc[-1]

total_days = (cumulative_df.index[-1] - cumulative_df.index[0]).days
cagr_sp500 = (sp500_cumulative_aligned.iloc[-1] / start_value) ** (365 / total_days) - 1
cagr_long   = (cumulative_df['pf_long'].iloc[-1] / start_value) ** (365 / total_days) - 1
cagr_ls     = (cumulative_df['pf_long_short'].iloc[-1] / start_value) ** (365 / total_days) - 1
cagr_mim    = (cumulative_df['pf_mimicking'].iloc[-1] / start_value) ** (365 / total_days) - 1

print(f"Annualized return pf_long: {cagr_long:.2%}")
print(f"Annualized return pf_long_short: {cagr_ls:.2%}")
print(f"Annualized return pf_mimicking: {cagr_mim:.2%}")
print(f"Annualized return S&P 500: {cagr_sp500:.2%}")

# Plot all three portfolios on the same graph + S&P 500 for comparison
plt.figure(figsize=(12,6))
plt.plot(cumulative_df.index, cumulative_df['pf_long'], label='Long Top 30')
plt.plot(cumulative_df.index, cumulative_df['pf_long_short'], label='Long-Short Top/Bottom 30')
plt.plot(cumulative_df.index, cumulative_df['pf_mimicking'], label='Factor Mimicking')
plt.plot(cumulative_df.index, sp500_cumulative_aligned, label='S&P 500', linestyle='--', color='black')

plt.suptitle("Growth of $1 Invested in Each Portfolio", fontsize=14)
plt.title(f"Rebalancing Monthly | {dates[0]} to {dates[-1]} | Advanced scoring strategy: {advanced_scoring}, Binary gate: {binary_gate}", fontsize=10)
plt.xlabel("Date")
plt.ylabel("Portfolio Value($)")    
plt.legend()
plt.grid(True)
plt.show()



    

