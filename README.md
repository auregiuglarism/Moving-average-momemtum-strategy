# Moving-average-momentum-strategy

## Data
The data used in this project is the daily closing price of all stocks that have been in the S&P 500 index from 2008 (post financial crisis) until now (February 2026). The data is sourced from Yahoo Finance and is available in the `data` folder of this repository.

## Binary Gate
Our stock universe is all the stocks that have been in the S&P 500 index from 2008 until now. To save computation time, we apply a binary gate condition to filter the stock universe. The binary gate condition is as follows:
1. Price > 200-day moving average
2. Relative strength index compared to the weekly S&P 500 index > 0

We will apply this condition every time we rebalance our portfolio, which is monthly in our case. The function to filter the stock universe based on the binary gate condition is implemented in the `binary_gate.py` file.

## Scoring
After filtering the stock universe using the binary gate condition, we score the remaining stocks based on a normal or advanced scoring strategy. We base ourselves again on the relative strength index compared to the weekly S&P 500 index and the 200-day moving average, but we also include the 1-year momentum and realized volatility in the advanced scoring strategy. The scoring function is implemented in the `scoring.py` file.