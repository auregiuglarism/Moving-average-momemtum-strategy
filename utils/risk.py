"""
Compute risk metrics for the assets and portfolios.
Does more risk equal more return ?
"""

import pandas as pd
import statsmodels.api as sm
import numpy as np

# --- Step 1: Compute Betas ---
def compute_asset_beta(asset_returns: pd.Series, factor_returns: pd.Series):
    """
    Estimate beta using time-series regression.

    r_i,t = alpha_i + beta_i f_t + epsilon_i,t
    """

    df = pd.concat([asset_returns, factor_returns], axis=1).dropna()
    df.columns = ["asset", "factor"]

    X = sm.add_constant(df["factor"])  # adds alpha
    y = df["asset"]

    model = sm.OLS(y, X).fit()

    beta = model.params["factor"]
    alpha = model.params["const"]

    return beta, alpha

def compute_betas(asset_data_list, factor_returns):
    """
    Compute betas for all assets.
    """

    betas = {}

    for asset_df in asset_data_list:

        if "Return" not in asset_df.columns:
            asset_df["Return"] = asset_df["Close"].pct_change()

        beta, alpha = compute_asset_beta(asset_df["Return"], factor_returns)

        ticker = asset_df["ticker"].iloc[0] if "ticker" in asset_df else len(betas)
        betas[ticker] = beta

    return pd.Series(betas)

# --- Step 2: Cross-sectional regression ---
def cross_sectional_regression(returns_t, betas):
    """
    Cross-sectional regression at time t:
    r_i,t = gamma0,t + gamma1,t * beta_i
    """

    df = pd.concat([returns_t, betas], axis=1).dropna()
    df.columns = ["return", "beta"]

    X = sm.add_constant(df["beta"])
    y = df["return"]

    model = sm.OLS(y, X).fit()

    gamma0 = model.params["const"]
    gamma1 = model.params["beta"]

    return gamma0, gamma1

def estimate_factor_risk_premium(returns_matrix, betas):
    gammas = []

    for t in returns_matrix.index:

        returns_t = returns_matrix.loc[t]
        gamma0, gamma1 = cross_sectional_regression(returns_t, betas)
        gammas.append(gamma1)

    gammas = pd.Series(gammas, index=returns_matrix.index)
    lambda_factor = gammas.mean()

    return gammas, lambda_factor

# --- Step 3: Test whether the factor is priced ---
# Does more risk equal more return ? Is the factor risk premium statistically different from zero ?
def test_factor_pricing(gammas):
    """
    Test whether factor risk premium is statistically different from zero.
    
    gammas = time series of gamma_1,t
    """

    T = len(gammas)

    lambda_factor = gammas.mean()
    std_gamma = gammas.std()

    t_stat = lambda_factor / (std_gamma / np.sqrt(T))

    return lambda_factor, t_stat