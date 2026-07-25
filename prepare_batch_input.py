"""
Prepare the Correct Batch Input for Vertex AI AutoML Forecasting
Appends null target rows for the forecast horizon to historical data.
"""
import pandas as pd
from datetime import timedelta
import os
from google.cloud import storage

# CONFIG
PROJECT_ID = "finance-502004"
BUCKET_NAME = "cloud-ai-platform-5198f7b8-0786-40a1-802e-78049446b994"
LOCAL_HISTORY = os.path.join(os.path.dirname(__file__), "gold_price_forecast.csv")
LOCAL_BATCH_INPUT = os.path.join(os.path.dirname(__file__), "gold_batch_input.csv")
GCS_DESTINATION = "data/gold_batch_input.csv"
HORIZON = 14

def prepare():
    print(f"📄 Reading history from {LOCAL_HISTORY}...")
    df = pd.read_csv(LOCAL_HISTORY)
    df['date'] = pd.to_datetime(df['date'])

    last_date = df['date'].max()
    print(f"🕒 Last historical date: {last_date.date()}")

    # Create future rows with NULL price
    future_dates = [last_date + timedelta(days=i) for i in range(1, HORIZON + 1)]
    future_df = pd.DataFrame({
        'date': future_dates,
        'series_id': 'GOLD',
        'price': None
    })

    # Combine
    batch_input = pd.concat([df, future_df])

    # Format date as string YYYY-MM-DD for CSV
    batch_input['date'] = batch_input['date'].dt.strftime('%Y-%m-%d')

    batch_input.to_csv(LOCAL_BATCH_INPUT, index=False)
    print(f"✅ Created {LOCAL_BATCH_INPUT} with {len(future_df)} null target rows.")

    # Upload to GCS
    client = storage.Client(project=PROJECT_ID)
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(GCS_DESTINATION)
    blob.upload_from_filename(LOCAL_BATCH_INPUT)
    print(f"🚀 Uploaded to gs://{BUCKET_NAME}/{GCS_DESTINATION}")

if __name__ == "__main__":
    prepare()
