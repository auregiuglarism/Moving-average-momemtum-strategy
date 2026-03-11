"""
Analyze data quality issues in the asset files
"""
import pandas as pd
import os

data_folder = 'Data/Assets'

print("=" * 80)
print("DATA QUALITY ANALYSIS")
print("=" * 80)

extreme_returns = []
data_gaps = []
price_anomalies = []

for filename in sorted(os.listdir(data_folder)):
    if filename.endswith('.csv'):
        ticker = filename.replace('yfinance_', '').replace('.csv', '')
        try:
            asset_df = pd.read_csv(os.path.join(data_folder, filename), parse_dates=['date'], index_col='date')
            asset_df = asset_df.sort_index()

            if len(asset_df) == 0:
                continue

            # Check for extreme monthly returns
            prices_monthly = asset_df['price'].resample('ME').last()
            monthly_return = prices_monthly.pct_change()

            max_ret = monthly_return.max()
            min_ret = monthly_return.min()

            if max_ret > 1.0 or min_ret < -0.75:
                extreme_returns.append((ticker, max_ret, min_ret))

            # Check for data gaps
            daily_returns = asset_df['price'].pct_change()
            huge_gaps = daily_returns[abs(daily_returns) > 0.5]
            if len(huge_gaps) > 0:
                data_gaps.append((ticker, len(huge_gaps)))

        except Exception as e:
            print(f"Error processing {ticker}: {e}")

print("\n1. STOCKS WITH EXTREME MONTHLY RETURNS (>100% or <-75%)")
print("-" * 80)
extreme_returns.sort(key=lambda x: abs(x[1]), reverse=True)
for ticker, max_ret, min_ret in extreme_returns[:20]:
    print(f"{ticker:6s}: Max {max_ret*100:7.2f}% | Min {min_ret*100:7.2f}%")

print(f"\nTotal: {len(extreme_returns)} stocks with extreme returns")

print("\n2. STOCKS WITH DAILY GAPS > 50% (Possible data errors or delisting)")
print("-" * 80)
data_gaps.sort(key=lambda x: x[1], reverse=True)
for ticker, num_gaps in data_gaps[:20]:
    print(f"{ticker:6s}: {num_gaps:3d} days with >50% moves")

print(f"\nTotal: {len(data_gaps)} stocks with extreme daily moves")

print("\n" + "=" * 80)
print("RECOMMENDATIONS:")
print("=" * 80)
print("""
1. INVESTIGATE DATA QUALITY
   - Check if extreme returns are real or data errors
   - Verify stock splits are handled correctly
   - Check for delisting dates and price discontinuities

2. APPLY DATA FILTERING
   - Winsorize monthly returns at ±50% (cap extreme values)
   - Remove stocks with suspicious data patterns
   - Exclude stocks with delisting events

3. VALIDATE METHODOLOGY
   - This strategy seems to "predict" extreme moves
   - This might indicate look-ahead bias
   - Or selection of winners based on underlying factors

4. CONSIDER
   - Survivorship bias (only stocks that survived made it to S&P 500)
   - Transaction costs (buying/selling 30+ stocks monthly is expensive)
   - Slippage and execution (backtests assume perfect fills)
""")
