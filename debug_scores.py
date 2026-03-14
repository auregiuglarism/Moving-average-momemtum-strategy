"""
Debug script to analyze score anomalies around 2010
"""
import pandas as pd
import json

# Load the rebalancing log
with open('logs/rebalancing_log.json', 'r') as f:
    log = json.load(f)

# Load the CSV log for easier viewing
csv_log = pd.read_csv('logs/rebalancing_log.csv')

print("=" * 80)
print("ANOMALY DETECTION: Returns and Score Issues")
print("=" * 80)

# Find anomalies (period returns > 0.1 or < -0.1)
anomalies = csv_log[abs(csv_log['period_return']) > 0.1].copy()
anomalies['date'] = pd.to_datetime(anomalies['date'])
anomalies = anomalies.sort_values('date')

print("\nANOMALOUS RETURNS (>10% or <-10%):")
print(anomalies[['date', 'period_return', 'num_bought', 'num_sold', 'bought_avg_score', 'sold_avg_score']].to_string())

print("\n" + "=" * 80)
print("EXTREME SCORES DETECTED IN 2010:")
print("=" * 80)

# Load the 2010 asset scores
assets_20100327 = pd.read_csv('logs/assets_scores_20100327.csv')
print("\n2010-03-27 Asset Scores (Top 10):")
print(assets_20100327.head(10).to_string(index=False))

assets_20100126 = pd.read_csv('logs/assets_scores_20100126.csv')
print("\n2010-01-26 Asset Scores (Top 10):")
print(assets_20100126.head(10).to_string(index=False))

# Show the problem
print("\n" + "=" * 80)
print("PROBLEM ANALYSIS:")
print("=" * 80)
print("""
The issue is that composite scores in 2010-03-27 are EXTREMELY high:
- MEE: 34.17 (should be < 1)
- TIE: 4.84 (should be < 1)
- Most others: 0.8 or less

This suggests the z-score normalization is broken. The scoring function
normalizes each asset's scores within its own time series (comparing it
against its own history), not against the universe of stocks.

When an asset like MEE or TIE has an extreme data point at a specific
date, it gets an extreme z-score compared to its own history. This can
result in scores of 30+ when they should be capped around 2-3 standard
deviations (a proper z-score).

SOLUTION: Need to normalize cross-sectionally at each rebalancing date
(across all assets), not within each asset's time series.
""")

print("\n" + "=" * 80)
print("DATA QUALITY CHECK:")
print("=" * 80)

# Check for any NaN or inf values in the normalization
print("\nChecking 2010-03-27 scores for data quality issues...")
with open('logs/assets_scores_20100327.csv', 'r') as f:
    content = f.read()
    if 'inf' in content.lower() or 'nan' in content.lower():
        print("FOUND NaN or Inf values!")
    else:
        print("No NaN/Inf values found")

    # Check for extremely high scores
    scores = assets_20100327['composite_score'].values
    print(f"Max score: {scores.max():.2f}")
    print(f"Min score: {scores.min():.2f}")
    print(f"Mean score: {scores.mean():.4f}")
    print(f"Std Dev: {scores.std():.4f}")
    print(f"Scores > 1.0: {(scores > 1.0).sum()} out of {len(scores)}")
    print(f"Scores > 2.0: {(scores > 2.0).sum()} out of {len(scores)}")
