"""
Compute portfolios of the top 30, bottom 30, and factor mimicking portfolios
based on the composite scores of the assets that passed the binary gate.
"""

import pandas as pd

def compute_portfolios_timeframe(scored_assets, top_n=30, timeframe='2009-01-01', rebalancing=15):
    """
    Build three portfolios at a given timeframe.

    Parameters
    ----------
    scored_assets : list[pd.DataFrame]
        List of asset dataframes containing Composite_Score.
        Index must be datetime.
    top_n : int
        Number of stocks in top portfolio.
    timeframe : str
        Target date for portfolio construction.
    rebalancing : int
        Number of days for rebalancing window (e.g., 15 for weekly, 30 for monthly).

    Returns
    -------
    pf_long : list
    pf_long_short : dict
    pf_mimicking : dict
    """

    target_date = pd.to_datetime(timeframe)

    timeframe_assets = []

    # --- Step 1: find assets with data near timeframe ---
    for asset in scored_assets:

        # find closest date in dataframe
        nearest_date = asset.index.get_indexer([target_date], method="nearest")[0]

        row_date = asset.index[nearest_date]

        # check if within ±7 days (weekly rebalancing) or +-15 days (monthly rebalancing)
        if abs((row_date - target_date).days) <= rebalancing:

            score = asset.iloc[nearest_date]["Composite_Score"]

            timeframe_assets.append({
                "asset": asset,
                "score": score
            })

    # convert to dataframe for easier sorting
    tf_df = pd.DataFrame(timeframe_assets)

    if tf_df.empty:
        raise ValueError("No assets found near the specified timeframe.")

    # --- Step 2: ranking ---
    tf_df = tf_df.sort_values("score", ascending=False)

    top_assets = tf_df.head(top_n)
    bottom_assets = tf_df.tail(top_n)

    # --- Portfolio 1: Long Top 30 ---
    pf_long = list(top_assets["asset"])

    # --- Portfolio 2: Long / Short ---
    pf_long_short = {
        "long": list(top_assets["asset"]),
        "short": list(bottom_assets["asset"])
    }

    # --- Portfolio 3: Factor mimicking ---
    n_half = len(tf_df) // 2

    top_half = tf_df.head(n_half)
    bottom_half = tf_df.tail(n_half)

    pf_mimicking = {
        "long": list(top_half["asset"]),
        "short": list(bottom_half["asset"])
    }

    return pf_long, pf_long_short, pf_mimicking

# Uncomment to test
if __name__ == "__main__":
    pass





