CREATE TABLE IF NOT EXISTS finance-502004.finance.gold_predictions (
prediction_time TIMESTAMP,
model_name STRING,
model_version STRING,
forecast_date DATE,
predicted_price FLOAT64,
source STRING
);
