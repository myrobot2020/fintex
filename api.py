"""
Minimal forecast API skeleton
Later you will point this at the real Endpoint
"""

from fastapi import FastAPI
from datetime import date

app = FastAPI(title="Gold Forecast API")

@app.get("/")
def root():
    return {"status": "ok", "service": "gold-forecast"}

@app.get("/forecast")
def forecast(horizon: int = 14):
    # TODO: replace with real Endpoint call once model is deployed
    return {
        "horizon": horizon,
        "generated_at": str(date.today()),
        "message": "Placeholder – connect to Vertex Endpoint after training finishes",
        "forecasts": []
    }

# Run later with:
# uvicorn api:app --reload --port 8080
