# Gold Price Forecasting on Vertex AI

## What it does
Forecasts daily gold prices using Vertex AI AutoML Forecasting, with a BigQuery ML ARIMA baseline for comparison.

## Architecture
Live prices (yfinance) → BigQuery + GCS → Vertex Dataset → AutoML Forecasting (Batch) + ARIMA baseline (Online) → Model Registry → Cloud Run API → Monitoring

## Model Usage
- **AutoML Forecasting**: Used for high-accuracy **Batch Predictions** via `run_batch_prediction.py`.
- **ARIMA_PLUS**: Used for **Real-time API** responses via BigQuery ML.

## Services used
- Datasets, Training, Model Registry, Batch Inference
- Feature Store, Experiments, Pipelines, Monitoring
- BigQuery ML (ARIMA_PLUS baseline)

## How new data flows
`live_ingestion.py` or `incremental_ingestion.py` pulls latest GC=F prices and MERGEs into BigQuery.

## Model comparison
ARIMA baseline vs AutoML Forecasting, tracked in Experiments.
Run `arima_eval.py` to see current baseline performance.
