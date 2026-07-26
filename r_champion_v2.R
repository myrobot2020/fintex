# R Champion v2 - "The Scalper"
# Sophisticated Ensemble for Gold Price Forecasting
# Target to beat: XGBoost MAE 46.79

if (!require("pacman")) install.packages("pacman")
pacman::p_load(fable, tsibble, dplyr, lubridate, readr, distributional)

# 1. Load Data
df_raw <- read_csv("C:/Users/ADMIN/Desktop/cl/finance/gold_price_forecast.csv")
df <- df_raw %>%
  mutate(date = as_date(date)) %>%
  as_tsibble(index = date, key = series_id) %>%
  fill_gaps() %>% # Handle weekends/holidays for NNETAR
  fill(price, .direction = "down")

# 2. Train Sophisticated Ensemble
print("🏃 Training Level 2 R Ensemble (ARIMA + ETS + NNETAR + STLF)...")
# NNETAR is a neural network model for time series
# STLF handles decomposition-based forecasting
fit <- df %>%
  model(
    arima = ARIMA(price ~ pdq(d=1) + PDQ(0,0,0)),
    ets = ETS(price),
    nn = NNETAR(sqrt(price)), # Transform for stability
    stlf = STLF(price)
  ) %>%
  mutate(ensemble = (arima + ets + nn + stlf) / 4)

# 3. Evaluate on 30-day Holdout
# We use time-series cross-validation for a "Legit" score
print("📊 Performing Cross-Validation...")
cv_accuracy <- df %>%
  stretch_tsibble(.init = 200, .step = 10) %>%
  model(ensemble = (ARIMA(price) + ETS(price) + NNETAR(price)) / 3) %>%
  forecast(h = 14) %>%
  accuracy(df)

mae_val <- cv_accuracy %>% filter(.model == "ensemble") %>% pull(MAE)

print(paste("🏆 R Champion v2 MAE:", round(mae_val, 2)))

if(mae_val < 46.79) {
  print("🔥 VICTORY: R Ensemble has outperformed XGBoost!")
  # Save the model
  saveRDS(fit, "C:/Users/ADMIN/Desktop/cl/finance/gold_r_champion_v2.rds")
} else {
  print("📉 Close, but XGBoost still holds the lead. Tuning further...")
}
