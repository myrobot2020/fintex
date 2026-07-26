"""
Data Source Layer
Fetches gold data from multiple tickers and aligns them.
"""
import yfinance as yf
import pandas as pd
import numpy as np

TICKERS = ["GC=F", "GLD"]

def fetch_raw_data(period="7d", interval="1m"):
    print(f"📡 Fetching {interval} data for {TICKERS} over {period}...")
    data = yf.download(TICKERS, period=period, interval=interval)

    if data.empty:
        raise ValueError("No data returned from Yahoo Finance.")

    # Get 'Close' prices
    df = data['Close'].copy()

    # Fill missing values (especially for GLD which has different trading hours)
    df = df.ffill().dropna()

    print(f"✅ Downloaded {len(df)} rows.")
    return df

def get_consensus_history(df):
    """
    Normalizes GLD to match GC=F scale and creates a consensus 'Price' column.
    """
    # Calculate rolling ratio to handle dynamic premium/discount
    df['ratio'] = df['GC=F'] / df['GLD']
    avg_ratio = df['ratio'].mean()

    # Scale GLD
    df['GLD_scaled'] = df['GLD'] * avg_ratio

    # Consensus is the average of the two (reduces single-source noise)
    df['consensus_price'] = (df['GC=F'] + df['GLD_scaled']) / 2

    # Final cleanup
    result = df[['GC=F', 'GLD', 'consensus_price']].copy()
    result.index.name = 'timestamp'
    return result

if __name__ == "__main__":
    raw = fetch_raw_data(period="5d", interval="1m")
    consensus = get_consensus_history(raw)
    print("\n--- Consensus Data (Last 5 mins) ---")
    print(consensus.tail())
    consensus.to_csv("C:/Users/ADMIN/Desktop/cl/finance/gold_consensus_raw.csv")
