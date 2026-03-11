"""
Logging utilities for tracking portfolio rebalancing events and asset details.
"""

import pandas as pd
import json
import os
from datetime import datetime


class RebalancingLogger:
    """Logs rebalancing events and asset information to CSV and JSON files."""

    def __init__(self, log_dir='Logs'):
        """
        Initialize the logger.

        Parameters
        ----------
        log_dir : str
            Directory to store log files
        """
        self.log_dir = log_dir
        self.rebalancing_log = []
        self.rebalancing_log_json = []
        self.asset_scores_by_date = {}
        self.portfolio_composition_snapshots = []

        # Create logs directory if it doesn't exist
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

    def log_rebalancing_event(self,
                             date,
                             period_return,
                             cumulative_return,
                             portfolio_value,
                             previous_portfolio_value,
                             bought_tickers,
                             bought_scores,
                             sold_tickers,
                             sold_scores,
                             portfolio_composition,
                             equal_weights=True):
        """
        Log a single rebalancing event.

        Parameters
        ----------
        date : datetime
            Date of rebalancing
        period_return : float
            Return for this period (e.g., 0.05 for 5%)
        cumulative_return : float
            Cumulative return from start (e.g., 0.25 for 25%)
        portfolio_value : float
            Current portfolio value
        previous_portfolio_value : float
            Portfolio value at previous rebalancing
        bought_tickers : list
            List of tickers that were bought
        bought_scores : dict
            Dict of {ticker: score} for bought assets
        sold_tickers : list
            List of tickers that were sold
        sold_scores : dict
            Dict of {ticker: score} for sold assets
        portfolio_composition : dict
            Dict of {ticker: score} for all assets in portfolio
        equal_weights : bool
            Whether positions use equal weights or score-weighted
        """
        portfolio_value_change = portfolio_value - previous_portfolio_value

        # Format sales and purchases as pipe-separated for CSV
        bought_str = " | ".join([f"{t}:{bought_scores[t]:.4f}" for t in bought_tickers]) if bought_tickers else "None"
        sold_str = " | ".join([f"{t}:{sold_scores[t]:.4f}" for t in sold_tickers]) if sold_tickers else "None"

        # Get average scores for bought vs sold
        bought_avg_score = sum(bought_scores.values()) / len(bought_scores) if bought_scores else None
        sold_avg_score = sum(sold_scores.values()) / len(sold_scores) if sold_scores else None

        # CSV log entry
        self.rebalancing_log.append({
            'date': date,
            'period_return': period_return,
            'cumulative_return': cumulative_return,
            'portfolio_value': portfolio_value,
            'portfolio_value_change': portfolio_value_change,
            'num_bought': len(bought_tickers),
            'num_sold': len(sold_tickers),
            'bought_tickers_scores': bought_str,
            'sold_tickers_scores': sold_str,
            'bought_avg_score': bought_avg_score,
            'sold_avg_score': sold_avg_score,
        })

        # JSON log entry with detailed buy/sell arrays and values
        bought_list = self._create_transaction_list(
            bought_tickers, bought_scores, portfolio_value, len(portfolio_composition), equal_weights
        )
        sold_list = self._create_transaction_list(
            sold_tickers, sold_scores, previous_portfolio_value, len(portfolio_composition), equal_weights
        )

        self.rebalancing_log_json.append({
            'date': date.isoformat(),
            'period_return': float(period_return),
            'cumulative_return': float(cumulative_return),
            'portfolio_value': float(portfolio_value),
            'portfolio_value_change': float(portfolio_value_change),
            'previous_portfolio_value': float(previous_portfolio_value),
            'num_bought': len(bought_tickers),
            'num_sold': len(sold_tickers),
            'bought_avg_score': float(bought_avg_score) if bought_avg_score else None,
            'sold_avg_score': float(sold_avg_score) if sold_avg_score else None,
            'bought': bought_list,
            'sold': sold_list,
        })

        # Store asset scores for this date
        self.asset_scores_by_date[date] = portfolio_composition

        # Create portfolio composition snapshot
        composition_snapshot = self._create_composition_snapshot(date, portfolio_composition, equal_weights)
        self.portfolio_composition_snapshots.append(composition_snapshot)

    def _create_transaction_list(self, tickers, scores, portfolio_value, num_assets, equal_weights):
        """
        Create a list of transactions with values.

        Parameters
        ----------
        tickers : list
            List of ticker symbols
        scores : dict
            Dict of {ticker: score}
        portfolio_value : float
            Total portfolio value to allocate
        num_assets : int
            Total number of assets in portfolio
        equal_weights : bool
            Whether to use equal or score-weighted allocation

        Returns
        -------
        list
            List of dicts with ticker, score, and value
        """
        if not tickers:
            return []

        transactions = []
        total_score = sum(scores.values()) if not equal_weights else 1.0

        for ticker in tickers:
            score = scores[ticker]

            if equal_weights:
                # Equal allocation per position
                value = portfolio_value / len(tickers) if tickers else 0
            else:
                # Score-weighted allocation
                weight = score / total_score
                value = portfolio_value * weight

            transactions.append({
                'ticker': ticker,
                'score': float(score),
                'value': float(value)
            })

        return transactions

    def _create_composition_snapshot(self, date, portfolio_composition, equal_weights):
        """
        Create a snapshot of portfolio composition at a given date.

        Parameters
        ----------
        date : datetime
            Rebalancing date
        portfolio_composition : dict
            Dict of {ticker: score}
        equal_weights : bool
            Whether using equal or score-weighted allocation

        Returns
        -------
        dict
            Snapshot including date, holdings, and allocation
        """
        num_holdings = len(portfolio_composition)
        total_score = sum(portfolio_composition.values()) if not equal_weights else 1.0

        holdings = []
        for ticker, score in portfolio_composition.items():
            if equal_weights:
                allocation_pct = (1.0 / num_holdings * 100) if num_holdings > 0 else 0
            else:
                allocation_pct = (score / total_score * 100) if total_score > 0 else 0

            holdings.append({
                'ticker': ticker,
                'score': float(score),
                'allocation_pct': float(allocation_pct),
                'position_type': 'long'  # For now, all are long in this context
            })

        return {
            'date': date.isoformat(),
            'num_holdings': num_holdings,
            'holdings': holdings
        }

    def save_logs(self):
        """Save all logs to CSV and JSON files."""
        if not self.rebalancing_log:
            print("No rebalancing events to log.")
            return

        # Save main rebalancing log (CSV)
        log_df = pd.DataFrame(self.rebalancing_log)
        log_path = os.path.join(self.log_dir, 'rebalancing_log.csv')
        log_df.to_csv(log_path, index=False)
        print(f"Saved rebalancing log to {log_path}")

        # Save main rebalancing log (JSON)
        json_log_path = os.path.join(self.log_dir, 'rebalancing_log.json')
        with open(json_log_path, 'w') as f:
            json.dump(self.rebalancing_log_json, f, indent=2)
        print(f"Saved rebalancing log (JSON) to {json_log_path}")

        # Save portfolio composition snapshots (JSON)
        composition_log_path = os.path.join(self.log_dir, 'portfolio_composition_evolution.json')
        with open(composition_log_path, 'w') as f:
            json.dump(self.portfolio_composition_snapshots, f, indent=2)
        print(f"Saved portfolio composition evolution to {composition_log_path}")

        # Save per-date asset scores
        for date, composition in self.asset_scores_by_date.items():
            date_str = date.strftime('%Y%m%d')
            scores_df = pd.DataFrame([
                {'ticker': ticker, 'composite_score': score}
                for ticker, score in composition.items()
            ]).sort_values('composite_score', ascending=False)

            scores_path = os.path.join(self.log_dir, f'assets_scores_{date_str}.csv')
            scores_df.to_csv(scores_path, index=False)

        print(f"Saved {len(self.asset_scores_by_date)} asset score files to {self.log_dir}")

    def get_portfolio_composition_dict(self, portfolio_assets):
        """
        Extract portfolio composition (tickers and scores) from asset DataFrames.

        Parameters
        ----------
        portfolio_assets : list
            List of asset DataFrames in the portfolio

        Returns
        -------
        dict
            Dict of {ticker: composite_score} for each asset
        """
        composition = {}
        # This will be populated by matching assets to their tickers
        # The assets are DataFrames, we need their names/indices
        return composition