import pandas as pd

# portfolios.py config
DEBUG_PORTFOLIOS=False

# main.py config
DEBUG_MAIN=False
DEBUG_MAIN_ABNORMAL=False

binary_gate=False
rebalancing_filter = 'monthly' 
rebalancing_portfolios = 30 
advanced_scoring = True
equal_weights=False
smoothing=True
ENABLE_LOGGING = False  # Enable rebalancing logging to CSV files

dates = pd.date_range(
        start="2020-01-01",
        end="2026-01-01",
        freq=f"{rebalancing_portfolios}D"   # Rebalancing
    )

start_value = 1.0 # Initial portfolio value