# Moving-average-momentum-strategy

## Data
The data used in this project is the daily closing price of all stocks that have been in the S&P 500 index from 2020 (post financial crisis) until now (January 2026). The data is sourced from Yahoo Finance and is available in the `data` folder of this repository.

Run the `data_validation.py` script in the `utils` folder to validate the data and ensure it meets the necessary quality standards for our analysis. This script checks for issues such as missing values, unrealistic price movements, and sufficient data length.

Run the `pull_tickers.py` script in the `data` folder to pull the list of tickers that are in the current S&P 500 index. This will be used to define our stock universe for the strategy.

Run the `pull_stocks.py` script in the `data` folder to pull the stocks from Yahoo Finance using the ticker list. This script will download the daily closing price data for all stocks in our universe and save them as CSV files in the `data` folder.

## Binary Gate
Our stock universe is all the stocks that have been in the S&P 500 index from 2020 until now. We apply a binary gate condition to filter the stock universe at every rebalancing. The binary gate condition is as follows:
1. Price > 200-day moving average
2. Relative strength index compared to the weekly S&P 500 index > 0

We will apply this condition every time we rebalance our portfolio, which is monthly in our case. The function to filter the stock universe based on the binary gate condition is implemented in the `binary_gate.py` file.

Keep in mind this feature will significantly increase the computation time. We recommend to set `binary_gate=False` in the `config.py` file if you want to run the code faster, it will not apply the binary gate condition and will score all stocks in the universe instead of filtering them first.

## Scoring
After filtering the stock universe using the binary gate condition, we score the remaining stocks based on a normal or advanced scoring strategy. We base ourselves again on the relative strength index compared to the weekly S&P 500 index and the 200-day moving average, but we also include the 1-year momentum and realized volatility in the advanced scoring strategy. The scoring function is implemented in the `scoring.py` file.

We normalize cross-sectionally and winsorize the scores if advanced scoring is enabled. Finally we combine all the scores into a final composite score and rank the stocks based on this composite score. 

## Portfolio Construction
We construct our portfolio by selecting the top 30 stocks based on the composite score and assigning them equal weights. We thus have:
- pf_long: the long portfolio, which consists of the top 30 stocks based on the composite score
- pf_ls_short: the long-short portfolio, which consists of the top 30 and bottom 30 stocks based on the composite score
- pf_mimicking: the mimicking portfolio, which consists of the top 50% and bottom 50% stocks based on the composite score.
 We rebalance our portfolio monthly, which means we will update our stock selection and weights every month based on the latest scores. The portfolio construction and rebalancing logic is implemented in the `portfolio.py` file.