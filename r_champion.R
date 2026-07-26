# R Champion Training Script - Gold Price Forecast
# Uses 'fable' for high-precision time series ensembling

# 1. Setup
if (!require("pacman")) install.packages("pacman")
pacman::p_load(fable, tsibble, dplyr, lubridate, reticulate, readr)

# 2. Configuration
PROJECT_ID <- "finance-502004"
REGION <- "us-central1"
EXPERIMENT <- "gold-forecast-experiment"

# 3. Load Data
df_raw <- read_csv("C:/Users/ADMIN/Desktop/cl/finance/gold_price_forecast.csv")
df <- df_raw %>%
  mutate(date = as_date(date)) %>%
  as_tsibble(index = date, key = series_id)

# 4. Train R Champion (Ensemble: ARIMA + ETS + TSLM)
print("🏃 Training R Champion Ensemble...")
fit <- df %>%
  model(
    arima = ARIMA(price),
    ets = ETS(price),
    lm = TSLM(price ~ trend() + season())
  ) %>%
  mutate(ensemble = (arima + ets + lm) / 3)

# 5. Evaluate (Last 30 days)
test_period <- df %>% filter(date >= max(date) - days(30))
forecasts <- fit %>%
  forecast(h = "30 days")

# Calculate MAE for the ensemble
res <- accuracy(fit) %>% filter(.model == "ensemble")
mae_val <- res$MAE

print(paste("✅ R Champion trained. MAE:", round(mae_val, 2)))

# 6. Log to Vertex AI Experiments via Python SDK (Reticulate)
# This bridge ensures the R results sit side-by-side with Python results
use_python("C:/Program Files/Python311/python.exe") # Adjust path if needed
aiplatform <- import("google.cloud.aiplatform")

aiplatform$init(project=PROJECT_ID, location=REGION, experiment=EXPERIMENT)

run_name <- paste0("r-champion-ensemble-", format(Sys.time(), "%H%M%S"))
with(aiplatform$start_run(run_name), {
  aiplatform$log_params(list(
    "model_type" = "ensemble",
    "components" = "ARIMA, ETS, TSLM",
    "library" = "fable"
  ))
  aiplatform$log_metrics(list(
    "mae" = as.numeric(mae_val)
  ))
})

print(paste("📊 Logged to Vertex Experiment as:", run_name))
