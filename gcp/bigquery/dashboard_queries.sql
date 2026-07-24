SELECT date, price
FROM finance-502004.finance.gold_price_forecast
ORDER BY date DESC LIMIT 30;

SELECT MAX(date) AS last_price_date,
DATE_DIFF(CURRENT_DATE(), MAX(date), DAY) AS days_stale
FROM finance-502004.finance.gold_price_forecast;

SELECT DATE(forecast_timestamp) AS forecast_date,
forecast_value AS predicted_price,
prediction_interval_lower_bound AS lower_bound,
prediction_interval_upper_bound AS upper_bound
FROM ML.FORECAST(
MODEL finance-502004.finance.gold_arima_baseline,
STRUCT(14 AS horizon, 0.95 AS confidence_level)
)
ORDER BY forecast_timestamp;

SELECT prediction_time, model_name, forecast_date, predicted_price, source
FROM finance-502004.finance.gold_predictions
ORDER BY prediction_time DESC LIMIT 100;
