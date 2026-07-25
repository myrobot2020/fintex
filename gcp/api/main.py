"""
Gold Forecast API - Cloud Run
READY NOW for structure + health checks.
WAIT FOR ENDPOINT: replace VERTEX_ENDPOINT_ID before live predictions.
"""
import os
from datetime import datetime, date
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
try:
    from google.cloud import aiplatform
    from google.cloud import bigquery
    VERTEX_AVAILABLE = True
except ImportError:
    VERTEX_AVAILABLE = False

PROJECT_ID = os.getenv("PROJECT_ID", "finance-502004")
REGION = os.getenv("VERTEX_LOCATION", "us-central1")
ENDPOINT_ID = os.getenv("VERTEX_ENDPOINT_ID", "PLACEHOLDER_ENDPOINT_ID")
BQ_DATASET = os.getenv("BQ_DATASET", "finance")
BQ_TABLE_PREDICTIONS = os.getenv("BQ_TABLE_PREDICTIONS", "gold_predictions")

app = FastAPI(
    title="Gold Forecast API",
    description="Production forecast service backed by Vertex AI",
    version="0.1.0",
)

class ForecastPoint(BaseModel):
    date: str
    predicted_price: float
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None

class ForecastResponse(BaseModel):
    horizon: int
    generated_at: str
    model_source: str
    forecasts: List[ForecastPoint]
    note: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    service: str
    endpoint_configured: bool
    timestamp: str

def endpoint_is_ready() -> bool:
    return ENDPOINT_ID not in (None, "", "PLACEHOLDER_ENDPOINT_ID")

def log_prediction_to_bq(horizon: int, forecasts: list, source: str = "online"):
    if not VERTEX_AVAILABLE:
        return
    try:
        client = bigquery.Client(project=PROJECT_ID)
        table_id = f"{PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE_PREDICTIONS}"
        rows = []
        now = datetime.utcnow().isoformat()
        for f in forecasts:
            rows.append({
                "prediction_time": now,
                "model_name": "vertex-endpoint",
                "model_version": ENDPOINT_ID,
                "forecast_date": f.get("date"),
                "predicted_price": f.get("predicted_price"),
                "source": source,
            })
        if rows:
            client.insert_rows_json(table_id, rows)
    except Exception as e:
        print(f"Warning: failed to log predictions: {e}")

@app.get("/", response_model=HealthResponse)
def root():
    return HealthResponse(
        status="ok",
        service="gold-forecast-api",
        endpoint_configured=endpoint_is_ready(),
        timestamp=datetime.utcnow().isoformat() + "Z",
    )

@app.get("/health", response_model=HealthResponse)
def health():
    return root()

@app.get("/forecast", response_model=ForecastResponse)
def forecast(horizon: int = Query(14, ge=1, le=30)):
    """
    Main forecast entry point.
    Note: AutoML Forecasting models are optimized for Batch Prediction.
    This live endpoint uses the ARIMA_PLUS baseline for real-time response.
    """
    return forecast_arima(horizon)

@app.get("/forecast/arima")
def forecast_arima(horizon: int = Query(14, ge=1, le=30)):
    if not VERTEX_AVAILABLE:
        raise HTTPException(status_code=500, detail="google-cloud-bigquery not available")
    try:
        client = bigquery.Client(project=PROJECT_ID)
        sql = f"""
        SELECT
            DATE(forecast_timestamp) AS date,
            forecast_value AS predicted_price,
            prediction_interval_lower_bound AS lower_bound,
            prediction_interval_upper_bound AS upper_bound
        FROM ML.FORECAST(
            MODEL {PROJECT_ID}.{BQ_DATASET}.gold_arima_baseline,
            STRUCT({horizon} AS horizon, 0.95 AS confidence_level)
        )
        ORDER BY forecast_timestamp
        """
        rows = list(client.query(sql).result())
        forecasts = [
            ForecastPoint(
                date=str(r["date"]),
                predicted_price=float(r["predicted_price"]),
                lower_bound=float(r["lower_bound"]) if r["lower_bound"] is not None else None,
                upper_bound=float(r["upper_bound"]) if r["upper_bound"] is not None else None,
            )
            for r in rows
        ]
        log_prediction_to_bq(horizon, [f.model_dump() for f in forecasts], source="arima")
        return ForecastResponse(
            horizon=horizon,
            generated_at=datetime.utcnow().isoformat() + "Z",
            model_source="bigquery-ml-arima-plus",
            forecasts=forecasts,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"ARIMA forecast failed: {str(e)}")
