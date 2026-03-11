import pandas as pd

# portfolios.py config
DEBUG_PORTFOLIOS=True

# main.py config
DEBUG_MAIN=True
DEBUG_MAIN_ABNORMAL=False

binary_gate=False
rebalancing_filter = 'monthly' 
rebalancing_portfolios = 30 
advanced_scoring = False
equal_weights=True
smoothing=True

dates = pd.date_range(
        start="2009-01-01",
        end="2026-01-01",
        freq=f"30D"   # Rebalancing
    )

start_value = 1.0 # Initial portfolio value