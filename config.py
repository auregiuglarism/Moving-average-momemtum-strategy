import pandas as pd

# portfolios.py config
DEBUG_PORTFOLIOS=False

# main.py config
DEBUG_MAIN=False
DEBUG_MAIN_ABNORMAL=False

binary_gate=False
rebalancing_filter = 'monthly' # weekly, monthly
rebalancing_portfolios = 30 # 7, 30
advanced_scoring = False
equal_weights=True
ENABLE_LOGGING = True  # Enable rebalancing logging to CSV files

dates = pd.date_range(
        start="2009-01-01",
        end="2019-01-01",
        freq=f"{rebalancing_portfolios}D"   # Rebalancing
    )

weeks_per_year = 12  # 12: monthly, 52: weekly
start_value = 1.0 # Initial portfolio value