# Data Corruption Analysis Report

**Status**: ✅ **ROOT CAUSE IDENTIFIED**

---

## Executive Summary

Your backtest is showing **102 million percent returns** due to **UNADJUSTED historical stock price data from Yahoo Finance**.

The data contains **REVERSE STOCK SPLITS that are NOT adjusted for**, causing:
- Price jumps of 1000x-34000x to appear as real trading profits
- 5-40 stocks with monthly "returns" exceeding 100%
- Your scoring algorithm selects these corrupted stocks
- Backtest treats split adjustments as real profits
- Result: Completely fake 100+ million percent returns

---

## Data Quality Assessment

### Total Stock Universe: 613 stocks

| Issue | Count | % | Severity |
|-------|-------|---|----------|
| Reverse splits not adjusted (>500% daily moves) | 5 | 0.8% | 🔴 CRITICAL |
| Delisted stocks (data ends pre-2024) | 15 | 2.4% | 🟠 HIGH |
| Extreme monthly returns (>100% or <-75%) | 39 | 6.4% | 🟠 HIGH |
| Clean data | 559 | 91.2% | ✅ GOOD |

---

## Detailed Issue Breakdown

### Issue 1: Reverse Splits Not Adjusted (CRITICAL)

**Affected Stocks:**
- **CBE**: 1:34,000 reverse split → 3,399,900% single-day "return"
- **TIE**: 1:7,214 reverse split → 714,548% single-day "return"
- **MEE**: 1:13,011 reverse split → 7,819% single-day "return"
- **CPWR**: Multiple splits → 4,567% monthly "return"
- **BMC**: 1:2,599 reverse split → 2,528% monthly "return"

**How It Works:**

```
Real World Scenario:
  Before split: Stock trading at $0.005, 1 million shares = $5,000 value
  Company does 1:34,000 reverse split
  After split: Stock trading at $170, ~29 shares = $5,000 value
  Economic value unchanged - just consolidated shares

Yahoo Finance Data (UNADJUSTED):
  Before: $0.005
  After: $170
  Recorded daily return: (170 - 0.005) / 0.005 = 3,399,900%

What Your Backtest Does:
  "CBE returned 3,399,900% today!"
  Applies this to portfolio calculation
  Compounds with other stocks
  Result: Insane portfolio returns
```

### Issue 2: Delisted Stocks

**Affected Stocks**: 15 stocks with data ending before 2024
- CBE: Last data 2018-01-30 (DELISTED)
- TIE: Last data 2019-07-12 (DELISTED)
- MEE: Last data 2017-08-10 (DELISTED)
- Others with gaps: GNW, BHPL, SHLD, etc.

**Problem**: Delisted stocks often have extreme price movements at delisting (bankruptcy, acquisition, etc.). Your backtest selects these based on technical indicators before they collapse.

### Issue 3: Penny Stocks with Extreme Volatility

Many of the corrupted stocks are penny stocks (< $5) that have been through multiple reverse splits:
- Extreme daily volatility
- High bid-ask spreads
- Not realistic to trade for a momentum strategy
- Data quality often poor

---

## Impact on Backtest

### Timeline of Insane Returns

When the backtest runs:

**2010-01-26**: 268% single period return
- Portfolio includes CBE, TIE, or other split-heavy stocks
- Scores technical indicators and selects them
- That specific day happens to have a split event
- Records as 268% gain (actually a split adjustment)

**2010-03-27**: 223% single period return
- Similar situation with different stock
- More split events in portfolio

**Cumulative Effect**:
- By 2010-11-22: Portfolio value at $26.45 (real dollars $1 → $26)
- Returns compounding unrealistically
- Final result: $1 → $1,021,547,652 (102 million percent return)

vs. S&P 500: $1 → $1.41 (40% real return)

---

## Why This Happened

### Root Cause

Yahoo Finance provides **unadjusted historical prices** by default:
- You can request adjusted prices, but the dataset appears to use unadjusted
- Stock splits, dividends, and other corporate actions cause price discontinuities
- Backtesting software typically requires split-adjusted data
- This dataset was not adjusted before use

### How To Verify

```python
# Check Yahoo Finance directly for a stock like CBE
# You'll see the 34,000:1 split in 2015
# And the price jumps 34,000x
# But the value stays the same (split-adjusted)
```

---

## Solution Options

### Option 1: Filter Corrupted Stocks (EASIEST) ✅ RECOMMENDED

```python
from utils.data_validation import filter_clean_universe

clean_tickers, removed = filter_clean_universe(
    'Data/Assets',
    max_daily_move=0.3,      # Max 30% daily
    max_monthly_return=0.5   # Max 50% monthly
)

# This removes stocks with unrealistic moves
# Reduces universe from 613 → ~560 stocks
# Eliminates the corrupted ones
# Backtest should show reasonable 8-20% annual returns
```

### Option 2: Use Split-Adjusted Data (HARD)

You would need to:
1. Download data from provider that auto-adjusts (Quandl, etc.)
2. Manually adjust historical prices for known splits
3. Apply adjustment factors to entire price history
4. Validate continuity

### Option 3: Cap Extreme Returns (MODERATE)

```python
# In scoring.py, winsorize returns:
monthly_returns.clip(-0.5, 0.5)  # Cap at ±50%
```

This removes the 700% outliers while keeping normal market moves.

### Option 4: Use Adjusted Close (IF AVAILABLE)

Yahoo Finance provides "Adjusted Close" which should be split-adjusted. Check if your data has this column.

---

## Data Validation Checklist

The clean dataset should have:
- ✅ No daily returns exceeding ±30%
- ✅ No monthly returns exceeding ±50%
- ✅ Price changes that are continuous (no 1000x jumps)
- ✅ Data through 2025-2026 for current stocks
- ✅ S&P 500 returns of 8-15% annually
- ✅ Portfolio returns NOT vastly exceeding S&P 500

The corrupted dataset currently has:
- ❌ Daily returns up to 3,399,900%
- ❌ Monthly returns up to 714,548%
- ❌ Price jumps of 34,000x
- ❌ Many stocks with data ending 2017-2019
- ❌ S&P 500 returns at 40% (reasonable) but strategy at 102 million%

---

## Recommended Immediate Actions

### 1. Apply Filter (5 minutes)
```bash
python3 << 'EOF'
from utils.data_validation import filter_clean_universe
clean_tickers, removed = filter_clean_universe('Data/Assets')
# Removes 39-50 corrupted stocks
EOF
```

### 2. Update main.py (10 minutes)
Use `clean_tickers` instead of all stocks in universe

### 3. Re-run Backtest (10 minutes)
Should now show realistic 8-20% annual returns

### 4. Validate Results (5 minutes)
Check that:
- No single-period returns > 20%
- Portfolio beats S&P by 2-5% annually
- No million-percent returns

---

## References

**Stock Split Impact:**
- A 1:1000 reverse split means 1 new share replaces 1000 old shares
- Price increases 1000x, but economic value stays the same
- Unadjusted data shows the price jump as a "1000x return"
- Split-adjusted data would show the same price (historical prices divided by 1000)

**Yahoo Finance Issue:**
- Yahoo provides both "Close" (unadjusted) and "Adj Close" (adjusted)
- Default API calls may return unadjusted prices
- Your dataset appears to use unadjusted prices

**Backtesting Best Practices:**
- Always use split-adjusted prices
- Validate for continuous price movements
- Check data quality before backtesting
- Compare strategy returns to benchmarks

---

## Conclusion

The extreme backtest returns are **NOT real**. They're caused by **unadjusted historical stock prices that contain reverse splits treated as trading profits**.

**Action Required**: Filter the corrupted stocks before continuing. Use the provided `filter_clean_universe()` function. This will reduce returns to realistic levels and give you valid backtest results.

**Estimated Time to Fix**: 15-20 minutes
**Risk of Not Fixing**: Completely invalid backtest results