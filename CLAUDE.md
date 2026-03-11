# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **momentum-based portfolio backtesting system** that evaluates three portfolio construction strategies using S&P 500 constituent stocks from 2008-present:

1. **pf_long**: Long-only portfolio (buy top 30 stocks by score)
2. **pf_long_short**: Long-short portfolio (buy top 30, short bottom 30)
3. **pf_mimicking**: Factor-mimicking portfolio (buy/short top/bottom 50% by factor exposure)

The strategy combines technical factors (moving average, relative strength) with optional advanced factors (12-month momentum, volatility) to score stocks, then constructs equal-weighted or value-weighted portfolios that rebalance monthly or weekly.

## How to Run

```bash
# Install dependencies
pip install -r requirements.txt

# Run the backtest (uses config.py for all parameters)
python main.py

# Analyze data quality
python analyze_data_quality.py

# Run with specific config
DEBUG_MAIN=False python main.py
```

**Output:**
- Console: Performance metrics (cumulative returns, annualized returns, comparison to S&P 500)
- Plots: Portfolio growth chart comparing all three strategies vs S&P 500
- Logs (if ENABLE_LOGGING=True): CSV/JSON files in `Logs/` directory with rebalancing details

## Core Architecture

### Pipeline: Data → Binary Gate → Scoring → Portfolio Construction → Backtesting

**main.py** - Orchestrates the entire backtest:
1. Loads S&P 500 data and asset price data
2. **Data Validation**: Filters corrupted stocks (extreme moves, delisted, etc.)
3. **Binary Gate** (optional): Applies technical conditions to reduce universe
4. **Scoring**: Ranks remaining stocks using technical factors
5. **Portfolio Construction**: Selects top/bottom 30 stocks
6. **Backtest Loop**: Compounds returns over time, logs rebalancing events
7. **Reporting**: Prints performance metrics and plots results

### Key Modules

**utils/data_validation.py**
- `filter_clean_universe()`: Removes stocks with unrealistic price moves (>30% daily, >50% monthly)
- Identifies corrupted data from reverse stock splits, delistings, bankruptcies
- Reduces universe from ~613 stocks to ~543 clean stocks
- **Critical**: Called in main.py Step 0b before processing

**utils/binary_gate.py**
- Filters stock universe to those passing technical conditions
- Conditions: Price > 200-day MA AND RSI_vs_SP500 > 0
- `filter_stock_universe()`: Returns filtered tickers and asset data for a given date
- Only used if `binary_gate=True` in config

**utils/scoring.py**
- **Normal scoring**: 200-day MA score + relative strength score (vs S&P 500)
- **Advanced scoring**: Adds 12-month momentum and realized volatility
- `calculate_raw_scores()`: Computes raw factors from price data
- `normalize_scores_cross_sectional()`: **CRITICAL** - Normalizes scores across the asset universe at each date using z-scores
  - Groups by date, compares each asset to universe mean/std at that date
  - Caps z-scores at ±3 to prevent outliers
  - Uses pandas groupby for vectorization (performance-critical)
- `compute_composite_score()`: Combines factors into single score

**utils/portfolios.py**
- `compute_portfolios_timeframe()`: Builds three portfolios at a specific rebalance date
  - Selects top 30 (long) and bottom 30 (short) by composite score
  - Calculates period returns for each portfolio
  - Returns 7 values including `portfolio_info` dict for logging
- `build_portfolio_composition_dict()`: Maps internal asset indices back to ticker symbols

**utils/logging_rebalance.py**
- Tracks portfolio composition and rebalancing events
- Outputs: CSV (transaction log), JSON (detailed events + composition evolution)
- `log_rebalancing_event()`: Records buys, sells, returns, portfolio value at each rebalance
- `save_logs()`: Persists logs to disk

**utils/portfolio_tracker.py**
- Maintains portfolio state across rebalancing periods
- `get_buys_and_sells()`: Identifies which stocks were bought/sold between rebalances
- Maps internal asset representation to ticker symbols

### Configuration (config.py)

```python
binary_gate = False                    # Use binary gate filtering (True/False)
rebalancing_filter = 'monthly'         # Frequency: 'weekly' or 'monthly'
rebalancing_portfolios = 30            # Days between rebalances (30 = monthly, 7 = weekly)
advanced_scoring = False               # Include momentum and volatility factors
equal_weights = True                   # True = equal weight all holdings, False = momentum-weight
ENABLE_LOGGING = True                  # Output detailed logs
start_value = 1.0                      # Initial portfolio value ($1)
weeks_per_year = 12                    # 12 for monthly, 52 for weekly (used in annualization)
dates = pd.date_range(...)             # Backtest date range
```

## Critical Technical Details

### 1. Cross-Sectional Normalization (not Time-Series)

**PROBLEM**: Original code normalized each asset's scores against its own historical distribution, causing extreme outliers (MEE: 40.93, TIE: 4.84) that spiked returns.

**SOLUTION**: Changed `normalize_scores_cross_sectional()` to group by date and normalize within each date across all assets:

```python
# Wrong (old): normalized asset to its own history
# Correct (new): normalized asset to universe at each date
all_data.groupby(level=0).apply(normalize_group)  # Group by date index
```

**Key point**: Z-scores should compare asset to peers on same date, not to its own past.

### 2. Weekly Return Calculation

**PROBLEM**: Code was resampling to weekly, then using daily returns from last day of week, causing daily spikes to appear as weekly returns (268% single day = 268% "weekly").

**SOLUTION**: Calculate true weekly returns from resampled prices:

```python
# Wrong: asset_data['Return'] = pct_change(daily); resample().last()
# Correct: asset_prices_weekly = resample('ME').last(); pct_change()
```

This ensures returns match the time period of the rebalancing frequency.

### 3. Data Corruption from Unadjusted Stock Prices

**ISSUE**: Yahoo Finance data contains unadjusted prices - reverse stock splits create artificial price jumps (e.g., 1:34,000 split = 3,399,900% single-day "return").

**SOLUTION**: Applied `filter_clean_universe()` in main.py Step 0b to remove 70 stocks with unrealistic moves. Expected behavior:
- Filters universe: 613 → 543 stocks
- Removes corrupted data from splits, delistings, bankruptcies
- Reduces spurious returns from millions of % to realistic single digits

**Remaining considerations**: Some stocks may still have extreme moves due to penny stock volatility or penny stock delisting events. If returns still seem high, consider:
- Further reducing max_daily_move/max_monthly_return thresholds
- Excluding stocks trading below $5
- Checking if strategy is selecting survivors from recovery periods (2008-2010)

## Performance and Known Issues

### Expected Results (with clean data)
- pf_long: 8-20% annualized
- pf_long_short: 5-15% annualized
- S&P 500 (benchmark): 10-15% annualized

### Current Status (post-filtering)
- Data filtering implemented and working
- Backtest runs successfully with 543 clean stocks
- Results still higher than typical (5-15% target), may indicate:
  - Genuine momentum effect during recovery period (2009-2010)
  - Remaining data quality issues in penny stocks
  - Survivorship bias (only listed stocks survived to 2025)

## Data Files

- **Data/Assets/**: Individual stock price CSVs (yfinance_TICKER.csv)
  - Format: date, price, volume
  - Source: Yahoo Finance
  - Validation: Use `filter_clean_universe()` to assess quality

- **Data/S&P 500 Historical Data.csv**: Benchmark index
  - Used for relative strength calculations and comparison
  - Format: Date, Close, Change %

- **Logs/**: Generated during backtest (if ENABLE_LOGGING=True)
  - rebalancing_log.csv: Transaction log
  - rebalancing_log.json: Detailed events
  - portfolio_composition_evolution.json: Holdings over time
  - asset_scores_YYYY-MM-DD.csv: Factor scores per date

## Debugging Checklist

1. **Extreme returns (>100% annualized)**?
   - Check `filter_clean_universe()` is running (Step 0b main.py)
   - Verify removed_tickers shows 50-70 stocks filtered
   - Look at top scores - should be 0-1 range, not 40.93

2. **System freezes during scoring**?
   - This was caused by nested loops in normalization
   - Current code uses `groupby()` which is vectorized
   - If freezing returns, check asset count and consider reducing date range

3. **Portfolio values diverging dramatically from S&P 500**?
   - Check if selected stocks have extreme volatility
   - Run `analyze_data_quality.py` to see distribution of returns
   - Verify scoring logic isn't selecting penny stocks before bankruptcy

4. **Logs missing or not saving**?
   - Ensure ENABLE_LOGGING = True in config.py
   - Check Logs/ directory exists (created automatically)
   - Verify portfolio_info is returned from `compute_portfolios_timeframe()`

## Testing and Validation

- **No automated tests**: This is a research/backtesting system
- **Manual validation**: Compare results to known market data for test periods
- **Sanity checks**: Run with DEBUG_MAIN_ABNORMAL=True to spot unusual returns
- **Data analysis**: Use `analyze_data_quality.py` to inspect stock distributions

## Recent Changes and Fixes

1. **Data Filtering (main.py Step 0b)** ✅
   - Added `filter_clean_universe()` call before processing
   - Filters stocks with >30% daily or >50% monthly moves
   - Removes ~70 corrupted stocks, keeps 543 quality stocks

2. **Cross-Sectional Normalization (scoring.py)** ✅
   - Rewrote `normalize_scores_cross_sectional()` to use pandas groupby
   - Fixed extreme outliers (scores capped at ±3 std devs)
   - Improved performance from O(dates × assets) to O(dates)

3. **Return Calculation (scoring.py)** ✅
   - Changed to calculate returns from resampled prices, not daily returns
   - Ensures weekly/monthly returns match rebalancing frequency

4. **Logging System (logging_rebalance.py, portfolio_tracker.py)** ✅
   - Comprehensive CSV + JSON logging of rebalancing events
   - Tracks buys, sells, portfolio composition, scores per rebalance date

## Important Implementation Notes

- **Asset Indices**: Internally, assets are referenced by list index, not ticker. The `portfolio_info` dict stores this mapping for logging.
- **Timezone Awareness**: Dates are pandas DatetimeIndex without timezone info (assumes UTC)
- **Resampling Frequency**: Changed from weekly ('W') to monthly ('ME') in some places; verify config.py matches intended rebalancing
- **Return Compounding**: Portfolio values are multiplicative: `value *= (1 + period_return)`
- **Weighting**: All portfolios use equal weights unless `equal_weights=False` (value-weighted by momentum score)

## Future Improvements

1. Implement transaction costs and slippage
2. Add Sharpe ratio, max drawdown calculations
3. Test on other date ranges and asset universes
4. Compare to other momentum definitions (12-month, cross-sectional)
5. Investigate why penny stocks remain in filtered set
6. Add walk-forward testing instead of single backtest

## References

- **Report**: DATA_CORRUPTION_REPORT.md - Details on data issues and solutions
- **Debug Report**: DEBUGGING_REPORT.md - Technical details on fixes applied
- **Strategy Details**: README.md - Business logic of binary gate and scoring