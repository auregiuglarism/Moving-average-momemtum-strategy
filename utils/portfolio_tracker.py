"""
Portfolio tracking utilities to maintain composition history and calculate buys/sells.
"""

import pandas as pd


class PortfolioTracker:
    """Tracks portfolio composition across rebalancing periods."""

    def __init__(self):
        """Initialize the portfolio tracker."""
        self.composition_history = {}  # date -> {ticker: score}
        self.previous_composition = {}

    def update_portfolio(self, date, portfolio_assets, ticker_list, scored_assets_dict):
        """
        Update portfolio composition at a rebalancing date.

        Parameters
        ----------
        date : datetime
            Rebalancing date
        portfolio_assets : list
            List of asset DataFrames in the portfolio
        ticker_list : list
            List of tickers in the stock universe
        scored_assets_dict : dict
            Dict mapping ticker to scored asset DataFrame

        Returns
        -------
        dict
            Current portfolio composition {ticker: score}
        """
        current_composition = {}

        # Extract the most recent score for each asset in the portfolio
        for i, asset_df in enumerate(portfolio_assets):
            if i < len(ticker_list):
                ticker = ticker_list[i]
                if not asset_df.empty:
                    latest_score = asset_df['Composite_Score'].iloc[-1]
                    current_composition[ticker] = latest_score

        self.composition_history[date] = current_composition
        self.previous_composition = current_composition

        return current_composition

    def get_buys_and_sells(self, current_composition):
        """
        Compare current portfolio with previous to identify buys and sells.

        Parameters
        ----------
        current_composition : dict
            Current portfolio {ticker: score}

        Returns
        -------
        tuple
            (bought_tickers, bought_scores_dict, sold_tickers, sold_scores_dict)
        """
        previous_tickers = set(self.previous_composition.keys())
        current_tickers = set(current_composition.keys())

        bought_tickers = list(current_tickers - previous_tickers)
        sold_tickers = list(previous_tickers - current_tickers)

        bought_scores = {t: current_composition[t] for t in bought_tickers}
        sold_scores = {t: self.previous_composition[t] for t in sold_tickers}

        return bought_tickers, bought_scores, sold_tickers, sold_scores

    def map_assets_to_tickers(self, portfolio_assets, scored_assets, stock_universe):
        """
        Map asset DataFrames to their tickers using the stock universe list.

        Parameters
        ----------
        portfolio_assets : list
            List of asset DataFrames in portfolio
        scored_assets : list
            List of all scored asset DataFrames
        stock_universe : list
            List of tickers in stock universe

        Returns
        -------
        dict
            Mapping of asset DataFrame id to ticker
        """
        asset_to_ticker = {}

        for asset in portfolio_assets:
            for ticker, scored_asset in zip(stock_universe, scored_assets):
                if asset.equals(scored_asset):
                    asset_to_ticker[id(asset)] = ticker
                    break

        return asset_to_ticker