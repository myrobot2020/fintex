"""
Local Inference Layer
Loads the winner from the tournament and generates a real-time prediction.
"""
import pandas as pd
import pickle
import os
from data_prep import load_and_feature_engineer

MODEL_FILE = "C:/Users/ADMIN/Desktop/cl/finance/local_winner.pkl"

def run_inference():
    if not os.path.exists(MODEL_FILE):
        print("❌ No model found. Run local_tournament.py first.")
        return

    # 1. Load latest features (don't shift target for inference)
    df = load_and_feature_engineer()
    latest_row = df.tail(1)

    features = [c for c in df.columns if 'lag_' in c or 'rolling_' in c or c == 'returns']
    X_latest = latest_row[features]

    # 2. Load model
    with open(MODEL_FILE, "rb") as f:
        model = pickle.load(f)

    # 3. Predict
    prediction = model.predict(X_latest)[0]
    current_price = latest_row['consensus_price'].values[0]
    diff = prediction - current_price
    direction = "📈 UP" if diff > 0 else "📉 DOWN"

    print("\n--- NEXT-TICK PREDICTION ---")
    print(f"🕒 Time (Last Tick): {latest_row.index[0]}")
    print(f"💰 Current Price   : ${current_price:.2f}")
    print(f"🎯 Predicted Next  : ${prediction:.2f}")
    print(f"🚀 Expected Signal : {direction} (${diff:+.2f})")

if __name__ == "__main__":
    run_inference()
