"""
Data Preparation Layer
Transforms raw consensus data into feature-engineered datasets for models.
"""
import pandas as pd
import numpy as np
import os

RAW_FILE = "C:/Users/ADMIN/Desktop/cl/finance/gold_consensus_raw.csv"

def load_and_feature_engineer(file_path=RAW_FILE, target_horizon=1):
    """
    Creates lags and technical indicators.
    target_horizon=1 means predict next row (Next-Tick).
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Run data_source.py first to create {file_path}")

    df = pd.read_csv(file_path, index_col='timestamp', parse_dates=True)

    # 1. Target column (Shifted price)
    df['target'] = df['consensus_price'].shift(-target_horizon)

    # 2. Lag features (Last 10 ticks)
    for i in range(1, 11):
        df[f'lag_{i}'] = df['consensus_price'].shift(i)

    # 3. Momentum indicators
    df['rolling_mean_5'] = df['consensus_price'].rolling(5).mean()
    df['rolling_std_5'] = df['consensus_price'].rolling(5).std()

    # 4. Returns (pct change)
    df['returns'] = df['consensus_price'].pct_change()

    # Cleanup
    df = df.dropna()

    print(f"✅ Prepared dataset with {len(df)} rows and {len(df.columns)} columns.")
    return df

if __name__ == "__main__":
    prepared = load_and_feature_engineer()
    print("\n--- Prepared Features ---")
    print(prepared.tail(2))
    prepared.to_csv("C:/Users/ADMIN/Desktop/cl/finance/gold_final_features.csv")
