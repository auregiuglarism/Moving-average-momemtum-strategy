# Debugging Report: Extreme Returns Issue

## Summary
The backtest was producing unrealistic returns (102 million percent for pf_long, 920 million percent for pf_long_short). Investigation revealed **three layers of issues**:

---

## Issue 1: Scoring Normalization (✅ FIXED)
**Severity**: CRITICAL

### Problem
Composite scores were being normalized within each asset's time series instead of across the universe:
- MEE score reached 40.93 (should be ~0 to 1)
- TIE score reached 4.84 (should be ~0 to 1)
- Caused initial spikes in 2010

### Root Cause
The normalization was comparing each asset against its own historical distribution instead of against all assets on each date.

### Solution
✅ **FIXED** - Rewrote `normalize_scores_cross_sectional()` in `scoring.py` to:
- Group by date (cross-sectional)
- Normalize within each date group across all assets
- Cap z-scores at ±3 standard deviations

---

## Issue 2: Weekly/Monthly Return Calculation (✅ FIXED)
**Severity**: CRITICAL

### Problem
Daily percentage changes were being resampled to weekly/monthly with `.last()`:
```python
asset_data['Return'] = asset_data['price'].pct_change()  # DAILY returns
asset_data = asset_data.resample('W').last()  # Takes LAST value
```
- Selected daily return from last day of week/month
- If a stock jumped 268% on one day, that became the "weekly" return

### Root Cause
Mixing daily and weekly time periods without proper return calculation

### Solution
✅ **FIXED** - Calculate true weekly/monthly returns from resampled prices:
```python
asset_prices_weekly = asset_data['price'].resample('ME').last()
weekly_return = asset_prices_weekly.pct_change()  # Correct weekly return
```

---

## Issue 3: DATA CORRUPTION (❌ CRITICAL - REQUIRES ACTION)
**Severity**: CRITICAL

### Problem
The underlying data contains extreme moves that aren't real market data:
- **CBE**: 3,399,900% monthly return (342 days with >50% moves)
- **TIE**: 714,548% monthly return (197 days with >50% moves)
- **MEE**: 7,819% monthly return (168 days with >50% moves)
- **CPWR**: 4,567% monthly return (108 days with >50% moves)
- Total: 39 stocks with monthly returns exceeding 100%

### Root Cause
These are likely:
1. **Reverse stock splits** not adjusted for in the data
2. **Bankruptcy/delisting events** (price collapse/spike)
3. **Corporate actions** with price adjustments
4. **Data errors** from Yahoo Finance

### Impact
The backtest is selecting these corrupted stocks and treating the extreme moves as real profits. Example:
- If 30-stock portfolio includes stocks with average monthly returns of 100%+
- Compounding over 24 months gives unrealistic results

### Solution
**YOU MUST DO ONE OF**:

**Option A: Filter corrupted stocks (RECOMMENDED)**
```python
from utils.data_validation import filter_clean_universe

clean_tickers, removed = filter_clean_universe(
    'Data/Assets',
    max_daily_move=0.3,      # Max 30% daily move
    max_monthly_return=0.5   # Max 50% monthly return
)

# Use clean_tickers in your backtest instead of all stocks
```

**Option B: Winsorize (cap) extreme returns**
```python
from utils.data_validation import clean_asset_returns

# In scoring.py, after calculating returns:
asset_df = clean_asset_returns(asset_df, max_daily_move=0.3)
```

**Option C: Investigate individual stocks**
Check what happened to CBE, TIE, MEE, CPWR manually in Yahoo Finance or other sources to understand if these are real events.

---

## Quick Fixes to Apply

### 1. Add Data Validation to main.py
```python
from utils.data_validation import filter_clean_universe

# Before loading assets
clean_tickers, removed = filter_clean_universe('Data/Assets')
print(f"Filtered {len(removed)} corrupted stocks")

# Then in your stock universe loop, only use clean_tickers
```

### 2. Validate Results After Fix
After filtering corrupted data:
- Expected pf_long return: 5-20% annually
- Expected pf_long_short return: 8-25% annually
- Not millions of percent

---

## Files Modified/Created

**Modified:**
- `utils/scoring.py` - Fixed cross-sectional normalization

**Created:**
- `utils/data_validation.py` - Data validation functions
- `analyze_data_quality.py` - Data quality analysis script
- `DEBUGGING_REPORT.md` - This file

---

## Remaining Work

1. **IMMEDIATE**: Choose one approach above and filter the data
2. **Verify**: Run backtest again with filtered data - should get reasonable returns
3. **Investigate**: Manually check CBE, TIE, MEE in Yahoo Finance
4. **Document**: Update README with data quality notes
5. **Validate**: Compare results to S&P 500 returns (should be lower but not insanely higher)

---

## Expected Results After All Fixes

**Before fixes:**
- pf_long: 102,154,765% (impossible)
- pf_long_short: 920,801,957% (impossible)

**After filtering data:**
- pf_long: 8-20% annually
- pf_long_short: 5-15% annually
- S&P 500: 12-15% annually

The strategy should beat the benchmark slightly, but not by absurd margins.
