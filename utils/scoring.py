"""
Contains both normal and advanced scoring functions for the strategy.
"""
import pandas as pd

# --- Calculate Raw 200 Day Moving Average Score (Normal Scoring) ---
def calculate_raw_scores(asset_data, sp500_data, advanced=False, smoothing=False):
    # Mandatory return computation
    asset_data['Return'] = asset_data['Close'].pct_change()
   
    # 200-day moving average score
    window = 200
    asset_data['MA'] = asset_data['Close'].rolling(window=window).mean()
    asset_data['MA_Score'] = (asset_data['Close'] - asset_data['MA']) / asset_data['MA']

    # Weekly relative strength score
    # IMPORTANT: Calculate weekly returns correctly from prices, not from daily returns
    if smoothing:
        asset_data = asset_data.resample('ME').mean()
        sp500_data = sp500_data.resample('ME').mean()
    else:
        asset_data = asset_data.resample('ME').last()
        sp500_data = sp500_data.resample('ME').last()

    # Add advanced scores if present
    if advanced:
        asset_data['MMTM_Score'] = asset_data['Close'].pct_change(periods=12)
        asset_data['REA_Volatility'] = asset_data['Return'].rolling(window=12).std()

    asset_data = asset_data.dropna()
    asset_data = asset_data.join(sp500_data['Change %'], how='left')
    # positive = outperformed S&P 500, negative = underperformed S&P 500
    asset_data['RS_Score'] = asset_data['Return'] - asset_data['Change %']
    
    return asset_data

# --- Compute normalized Z-score for each factor (CROSS-SECTIONAL: across universe, not time) ---
def normalize_scores_cross_sectional(asset_data_list, advanced=False):
    """
    Normalize scores across the universe of assets at each date (cross-sectional),
    not within each asset's time series (which was causing extreme outliers).

    OPTIMIZED: Uses pandas groupby for vectorized operations instead of loops.

    Parameters
    ----------
    asset_data_list : list
        List of asset DataFrames to normalize together
    advanced : bool
        Whether to include advanced factors

    Returns
    -------
    list
        List of normalized asset DataFrames
    """
    if advanced:
        factor_list=['MA_Score', 'RS_Score', 'MMTM_Score', 'REA_Volatility']
    else:
        factor_list=['MA_Score', 'RS_Score']

    print(f"  Merging {len(asset_data_list)} assets for normalization...")

    # Add asset identifier to each dataframe
    for i, asset_df in enumerate(asset_data_list):
        asset_df['_asset_idx'] = i

    # Concat all into one DataFrame
    all_data = pd.concat(asset_data_list, ignore_index=False)

    print(f"  Normalizing across dates using groupby...")

    # Group by date and normalize within each group
    def normalize_group(group):
        for factor in factor_list:
            if factor in group.columns:
                mean = group[factor].mean()
                std = group[factor].std()
                if std > 0:
                    normalized = (group[factor] - mean) / std
                    # Cap z-scores at +/- 3
                    normalized = normalized.clip(-3, 3)
                    group[factor + '_Norm'] = normalized
                else:
                    group[factor + '_Norm'] = 0
        return group

    all_data_normalized = all_data.groupby(level=0, group_keys=False).apply(normalize_group)

    print(f"  Splitting back into individual assets...")

    # Split back into individual dataframes
    for i, asset_df in enumerate(asset_data_list):
        mask = all_data_normalized['_asset_idx'] == i
        normalized_df = all_data_normalized[mask].copy()

        # Add normalized columns back to original dataframe (with explicit index alignment)
        for factor in factor_list:
            norm_col = factor + '_Norm'
            if norm_col in normalized_df.columns:
                asset_df[norm_col] = normalized_df[norm_col].reindex(asset_df.index)

        # Remove temporary column
        if '_asset_idx' in asset_df.columns:
            asset_df.drop('_asset_idx', axis=1, inplace=True)

    return asset_data_list

# --- Winsorize Z-scores at 5th and 95th percentiles ---
def winsorize_scores(asset_data):
    for score in ['MA_Score_Norm', 'RS_Score_Norm', 'MMTM_Score_Norm', 'REA_Volatility_Norm']:
        if score in asset_data.columns:
            lower_bound = asset_data[score].quantile(0.05)
            upper_bound = asset_data[score].quantile(0.95)
            asset_data[score] = asset_data[score].clip(lower=lower_bound, upper=upper_bound)
    return asset_data

# --- Create final composite score ---
def create_final_composite_score(asset_data, advanced, weights):
    if advanced:
        factor_list=['MA_Score_Norm', 'RS_Score_Norm', 'MMTM_Score_Norm', 'REA_Volatility_Norm']
    else:
        factor_list=['MA_Score_Norm', 'RS_Score_Norm']
    asset_data['Composite_Score'] = 0
    for score, weight in zip(factor_list, weights):
        if score in asset_data.columns:
            asset_data['Composite_Score'] += weight * asset_data[score]
        else:
            # If normalized score doesn't exist, skip it (might be for the test file)
            pass
    return asset_data
    
# --- Main function to run the scoring process ---
def compute_scoring(asset_data_list, sp500_df, advanced=False, smoothing=False):
    weights = [0.5, 0.5] if not advanced else [0.3, 0.3, 0.2, 0.2]

    print(f"\nComputing scores for {len(asset_data_list)} assets...")
    print("Step 1: Calculating raw scores...")

    # Step 1: Calculate raw scores for all assets
    for i, asset_df in enumerate(asset_data_list):
        if i % max(1, len(asset_data_list) // 5) == 0:
            print(f"  Processed {i}/{len(asset_data_list)} assets...")
        asset_df = asset_df.sort_index()  # Ensure data is sorted by date
        asset_df = calculate_raw_scores(asset_df, sp500_df, advanced=advanced, smoothing=smoothing)
        asset_df.dropna(inplace=True)
        asset_data_list[i] = asset_df

    print("Step 2: Normalizing scores cross-sectionally...")
    # Step 2: Normalize cross-sectionally across the universe (not within each asset's history)
    asset_data_list = normalize_scores_cross_sectional(asset_data_list, advanced=advanced)

    print("Step 3: Creating composite scores...")
    # Step 3: Winsorize and create composite scores
    for i, asset_df in enumerate(asset_data_list):
        if advanced:
            asset_df = winsorize_scores(asset_df)
        asset_df = create_final_composite_score(asset_df, advanced=advanced, weights=weights)
        asset_data_list[i] = asset_df

    print("Scoring complete!")
    return asset_data_list

# Uncomment to test
if __name__ == "__main__":
    import os
    import glob

    # Get paths relative to this script file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)

    # Load multiple assets (needed for proper cross-sectional normalization)
    stock_files = glob.glob(os.path.join(project_dir, "data/stocks/*.csv"))[:5]  # Load first 5 stocks
    asset_list = []

    for stock_file in stock_files:
        asset = pd.read_csv(stock_file)
        asset = asset.iloc[2:]
        asset.rename(columns={"Price": "Date"}, inplace=True)
        asset["Date"] = pd.to_datetime(asset["Date"])
        asset.set_index("Date", inplace=True)
        asset = asset.astype(float)
        asset_list.append(asset.sort_index())

    sp500 = pd.read_csv(os.path.join(project_dir, 'data/sp500_historical.csv'), parse_dates=['Date'], index_col='Date')
    sp500['Change %'] = (
        sp500['Change %']
        .str.replace('%', '', regex=False)
        .astype(float) / 100
    )
    sp500 = sp500.sort_index()

    # Score all assets
    print(f"Testing with {len(asset_list)} assets...\n")
    scored_assets = []
    for i, asset in enumerate(asset_list):
        scored_asset = calculate_raw_scores(asset, sp500, advanced=True, smoothing=False)
        scored_asset.dropna(inplace=True)
        scored_assets.append(scored_asset)

    # Normalize across the universe
    scored_list = normalize_scores_cross_sectional(scored_assets, advanced=True)

    # Show results from first asset
    first_asset = scored_list[0]
    print("Columns after normalization:", first_asset.columns.tolist())
    print("\nSample normalized scores (first asset):\n", first_asset[['MA_Score_Norm', 'RS_Score_Norm']].head() if 'MA_Score_Norm' in first_asset.columns else "No normalized columns found")

    # Create composite scores
    for i, asset_df in enumerate(scored_list):
        asset_df = winsorize_scores(asset_df)
        asset_df = create_final_composite_score(asset_df, advanced=True, weights=[0.3, 0.3, 0.2, 0.2])
        scored_list[i] = asset_df

    print("\nFinal composite scores (first asset):\n", scored_list[0][['Composite_Score']].head())

