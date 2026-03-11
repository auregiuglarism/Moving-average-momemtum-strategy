import pandas as pd

# portfolios.py config
DEBUG_PORTFOLIOS=True

# main.py config
DEBUG_MAIN=True
DEBUG_MAIN_ABNORMAL=False
binary_gate=False
rebalancing_filter = 'monthly' # or 'monthly'
rebalancing_portfolios = 30 # 7, 30
advanced_scoring = False
dates = pd.date_range(
        start="2009-01-01",
        end="2026-01-01",
        freq=f"{rebalancing_portfolios}D"   # Rebalancing
    )