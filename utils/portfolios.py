"""
Compute portfolios of the top 30, bottom 30, and factor mimicking portfolios
based on the composite scores of the assets that passed the binary gate.
"""

import pandas as pd
from config import DEBUG_PORTFOLIOS

def compute_portfolios_timeframe(scored_assets, top_n=30, timeframe='2020-01-01', next_timeframe=None, rebalancing=30, equal_weights=True):
    """
    Build three portfolios at a given timeframe, measuring returns to the next timeframe.

    Parameters
    ----------
    scored_assets : list[pd.DataFrame]
        List of asset dataframes containing Composite_Score and prices.
        Index must be datetime.
    top_n : int
        Number of stocks in top portfolio.
    timeframe : str
        Target date for portfolio construction (rebalance date).
    next_timeframe : str
        Target date for measuring returns (next rebalance date).
    rebalancing : int
        Number of days for rebalancing window (30 for monthly).

    Returns
    -------
    pf_long : list
    pf_long_short : dict
    pf_mimicking : dict
    """

    target_date = pd.to_datetime(timeframe)
    next_date = pd.to_datetime(next_timeframe) if next_timeframe else None

    timeframe_assets = []

    # --- Step 1: find assets with data near timeframe ---
    for asset in scored_assets:
        # skip if the asset has no rows go to next asset
        if asset.empty:
            print("HIT, asset empty") if DEBUG_PORTFOLIOS else None
            continue

        start_date = target_date - pd.Timedelta(days=rebalancing)

        # find start_date <= all dates <= target_date
        past_dates = asset.index[(asset.index >= start_date) & (asset.index <= target_date)]
        print(f"Asset has {len(past_dates)} past dates before {target_date.strftime('%Y-%m-%d')}.") if DEBUG_PORTFOLIOS else None

        # skip if no past dates available go to next asset
        if past_dates.empty:
            print("HIT, no past dates available") if DEBUG_PORTFOLIOS else None
            continue

        # get the most recent past date (closest backward) - this is when we make the decision
        decision_date = past_dates[-1]
        row = asset.loc[decision_date]

        # check if within rebalancing days backward only
        if (target_date - decision_date).days <= rebalancing:
            score = row["Composite_Score"]
            price_at_decision = row["Close"]

            # Calculate actual forward return from decision date to next timeframe
            asset_return = None
            if next_date is not None:
                # Find the price at or nearest to next_date
                future_dates = asset.index[asset.index >= next_date]
                if len(future_dates) > 0:
                    measurement_date = future_dates[0]
                    price_at_measurement = asset.loc[measurement_date, "Close"]
                    # Calculate return: (price_end - price_start) / price_start
                    asset_return = (price_at_measurement - price_at_decision) / price_at_decision
            else:
                # No next timeframe specified, use Return column (for backward compatibility)
                asset_return = row["Return"]

            if asset_return is not None and not pd.isna(asset_return):
                timeframe_assets.append({
                    "asset": asset,
                    "score": score,
                    "return": asset_return
                })

    # convert to dataframe for easier sorting
    tf_df = pd.DataFrame(timeframe_assets)

    if not tf_df.empty:
        # --- Step 2: ranking ---
        tf_df = tf_df.sort_values("score", ascending=False)

        n_assets = len(tf_df)
        top_n = min(top_n, max(1, int(n_assets * 0.3)))  # 30% of universe

        top_assets = tf_df.head(top_n)
        bottom_assets = tf_df.tail(top_n)

        print("Top returns:", top_assets["return"].head()) if DEBUG_PORTFOLIOS else None
        print("Bottom returns:", bottom_assets["return"].head()) if DEBUG_PORTFOLIOS else None      

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

        # Extract ticker information for logging
        portfolio_info = {
            'top_assets': top_assets,
            'bottom_assets': bottom_assets,
            'top_half': top_half,
            'bottom_half': bottom_half
        }

        return pf_long, pf_long_short, pf_mimicking, pf_long_returns, pf_long_short_returns, pf_mimicking_returns, portfolio_info
    else:
        print("No assets found for that timeframe. Going to the next timeframe.") if DEBUG_PORTFOLIOS else None
        return None, None, None, None, None, None, None


def build_portfolio_composition_dict(portfolio_info, scored_assets, stock_universe):
    """
    Build a dictionary mapping tickers to their composite scores for logging.

    Parameters
    ----------
    portfolio_info : dict
        Portfolio information returned from compute_portfolios_timeframe
    scored_assets : list
        List of all scored asset DataFrames
    stock_universe : list
        List of tickers corresponding to scored_assets

    Returns
    -------
    dict
        {ticker: composite_score} for all assets in the portfolio
    """
    if portfolio_info is None:
        return {}

    composition = {}

    # Create a mapping of asset DataFrames to tickers
    asset_to_ticker = {}
    for ticker, scored_asset in zip(stock_universe, scored_assets):
        # Use id to track DataFrame identity
        for asset in scored_assets:
            if asset.equals(scored_asset):
                asset_to_ticker[id(asset)] = ticker
                break

    # Extract all assets that were included in portfolio decisions
    all_portfolio_assets = []
    if 'top_assets' in portfolio_info:
        for _, row in portfolio_info['top_assets'].iterrows():
            all_portfolio_assets.append((row['asset'], row['score']))
    if 'bottom_assets' in portfolio_info:
        for _, row in portfolio_info['bottom_assets'].iterrows():
            all_portfolio_assets.append((row['asset'], row['score']))

    # Map back to tickers using scored_assets list
    for asset, score in all_portfolio_assets:
        for i, scored_asset in enumerate(scored_assets):
            if asset.equals(scored_asset):
                if i < len(stock_universe):
                    ticker = stock_universe[i]
                    composition[ticker] = float(score)
                break

    return composition







