"""
Contains both normal and advanced scoring functions for the strategy.
"""
import pandas as pd


# --- Calculate Raw 200 Day Moving Average Score (Normal Scoring) ---
def calculate_raw_scores(asset_data, sp500_data, advanced=False, smoothing=False):
    # Mandatory return computation
    asset_data['Return'] = asset_data['price'].pct_change()
   
    # 200-day moving average score
    window = 200
    asset_data['MA'] = asset_data['price'].rolling(window=window).mean()
    asset_data['MA_Score'] = (asset_data['price'] - asset_data['MA']) / asset_data['MA']

    # Weekly relative strength score
    if smoothing:
        asset_data = asset_data.resample('W').mean()
        sp500_data = sp500_data.resample('W').mean()
    else:
        asset_data = asset_data.resample('W').last()
        sp500_data = sp500_data.resample('W').last()
    asset_data = asset_data.join(sp500_data['Change %'], how='inner') # SP500 return
    # positive = outperformed S&P 500, negative = underperformed S&P 500
    asset_data['RS_Score'] = asset_data['Return'] - asset_data['Change %'] 

    if advanced:
        # 12-month momentum score
        asset_data['MMTM_Score'] = asset_data['price'].pct_change(periods=52) # 52 weeks in a year

        # Realized volatility (21 trading days in a month)
        asset_data['REA_Volatility'] = asset_data['Return'].rolling(window=4).std() # 4 weeks in a month
    
    return asset_data

# --- Compute normalized Z-score for each factor ---
def normalize_scores_cross_sectional(asset_data, advanced=False):
    if advanced:
        factor_list=['MA_Score', 'RS_Score', 'MMTM_Score', 'REA_Volatility']
    else:
        factor_list=['MA_Score', 'RS_Score']
    for score in factor_list:
        asset_data[score + '_Norm'] = (asset_data[score] - asset_data[score].mean()) / asset_data[score].std()
    return asset_data

# --- Winsorize Z-scores at 5th and 95th percentiles ---
def winsorize_scores(asset_data):
    for score in ['MA_Score_Norm', 'RS_Score_Norm', 'MMTM_Score_Norm', 'REA_Volatility_Norm']:
        lower_bound = asset_data[score].quantile(0.05)
        upper_bound = asset_data[score].quantile(0.95)
        asset_data[score] = asset_data[score].clip(lower=lower_bound, upper=upper_bound)
    return asset_data

# --- Create final composite score ---
def create_final_composite_score(asset_data, advanced, weights):
    if advanced:
        factor_list=['MA_Score', 'RS_Score', 'MMTM_Score', 'REA_Volatility']
    else:
        factor_list=['MA_Score', 'RS_Score']
    asset_data['Composite_Score'] = 0
    for score, weight in zip(factor_list, weights):
        asset_data['Composite_Score'] += weight * asset_data[score]
    return asset_data
    
# --- Main function to run the scoring process ---
def compute_scoring(asset_data_list, sp500_df, advanced=False):
    weights = [0.5, 0.5] if not advanced else [0.3, 0.3, 0.2, 0.2]
    
    for i, asset_df in enumerate(asset_data_list):
        asset_df = asset_df.sort_index()  # Ensure data is sorted by date
        asset_df = calculate_raw_scores(asset_df, sp500_df, advanced=advanced, smoothing=False)
        asset_df.dropna(inplace=True)
        asset_df = normalize_scores_cross_sectional(asset_df, advanced=advanced)
        if advanced:
            asset_df = winsorize_scores(asset_df)
        asset_df = create_final_composite_score(asset_df, advanced=advanced, weights=weights)
        asset_data_list[i] = asset_df # Replace original DataFrame with scored DataFrame in the list

    return asset_data_list

# Uncomment to test
if __name__ == "__main__":
    asset = pd.read_csv('Data/Assets/yfinance_A.csv', parse_dates=['date'], index_col='date')
    sp500 = pd.read_csv('Data/S&P 500 Historical Data.csv', parse_dates=['Date'], index_col='Date')
    sp500['Change %'] = (
        sp500['Change %']
        .str.replace('%', '', regex=False)
        .astype(float) / 100
    )
    asset = asset.sort_index()
    sp500 = sp500.sort_index()
    scored_asset = calculate_raw_scores(asset, sp500, advanced=True, smoothing=False)
    scored_asset.dropna(inplace=True)
    normalized_asset = normalize_scores_cross_sectional(scored_asset, advanced=True)
    winsorized_asset = winsorize_scores(normalized_asset)
    final_scored_asset = create_final_composite_score(winsorized_asset, advanced=True, weights=[0.3, 0.3, 0.2, 0.2])
    print(final_scored_asset.head())

