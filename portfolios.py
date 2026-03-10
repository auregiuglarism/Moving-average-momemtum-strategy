"""
Compute portfolios of the top 30, bottom 30, and factor mimicking portfolios
based on the composite scores of the assets that passed the binary gate.
"""

import pandas as pd

def compute_portfolios_timeframe(scored_assets, top_n=30, timeframe='2009-01-01', rebalancing=15, equal_weights=True):
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
        # skip if the asset has no rows (he maybe wasn't in the S&P 500 at that time)
        if asset.empty:
            continue

        # find all dates <= target_date
        past_dates = asset.index[asset.index <= target_date]

        # skip if no past dates available
        if past_dates.empty:
            continue

        # get the most recent past date (closest backward)
        nearest_date = past_dates[-1]
        row = asset.loc[nearest_date]

        # check if within rebalancing days backward only
        if (target_date - nearest_date).days <= rebalancing:
            score = row["Composite_Score"]
            asset_return = row["Return"]

            timeframe_assets.append({
                "asset": asset,
                "score": score,
                "return": asset_return
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
    if equal_weights:
        pf_long_returns = top_assets["return"].mean()
    else:
        weights = top_assets["score"] / top_assets["score"].sum()
        pf_long_returns = (weights * top_assets["return"]).sum()

    # --- Portfolio 2: Long / Short ---
    pf_long_short = {
        "long": list(top_assets["asset"]),
        "short": list(bottom_assets["asset"])
    }
    if equal_weights:
        pf_long_short_returns = top_assets["return"].mean() - bottom_assets["return"].mean()
    else:
        long_weights = top_assets["score"] / top_assets["score"].sum()
        short_weights = bottom_assets["score"] / bottom_assets["score"].sum()
        pf_long_short_returns = (long_weights * top_assets["return"]).sum() - (short_weights * bottom_assets["return"]).sum()

    # --- Portfolio 3: Factor mimicking ---
    n_half = len(tf_df) // 2

    top_half = tf_df.head(n_half)
    bottom_half = tf_df.tail(n_half)

    pf_mimicking = {
        "long": list(top_half["asset"]),
        "short": list(bottom_half["asset"])
    }
    if equal_weights:
        pf_mimicking_returns = top_half["return"].mean() - bottom_half["return"].mean()
    else:
        long_weights = top_half["score"] / top_half["score"].sum()
        short_weights = bottom_half["score"] / bottom_half["score"].sum()
        pf_mimicking_returns = (long_weights * top_half["return"]).sum() - (short_weights * bottom_half["return"]).sum()

    # Uncomment to test
    # print(f"portfolio pf_long has {len(pf_long)} assets.")
    # print(f"portfolio pf_long_short has {len(pf_long_short['long'])} long assets and {len(pf_long_short['short'])} short assets.")
    # print(f"portfolio pf_mimicking has {len(pf_mimicking['long'])} long assets and {len(pf_mimicking['short'])} short assets.")
    # print(f"Average return of pf_long: {pf_long_returns:.2%}")
    # print(f"Average return of pf_long_short: {pf_long_short_returns:.2%}")
    # print(f"Average return of pf_mimicking: {pf_mimicking_returns:.2%}") 

    return pf_long, pf_long_short, pf_mimicking, pf_long_returns, pf_long_short_returns, pf_mimicking_returns






