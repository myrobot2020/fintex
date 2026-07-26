# Plumber API for R Champion Model
# This is the 'Second-Level' entry point for R-based HF (ish) inference

library(plumber)
library(jsonlite)
library(fable)
library(tsibble)
library(dplyr)
library(lubridate)

# Load the model artifact (Assuming it was saved as an .rds file)
# In a real Vertex deployment, this file is copied into the container
# model <- readRDS("gold_ensemble_model.rds")

#* @get /health
function() {
  list(status = "ok", service = "r-forecast-engine")
}

#* @post /predict
#* @param instances The input data from Vertex AI
function(req) {
  # Vertex AI sends data in a specific JSON format: {"instances": [...]}
  input_data <- jsonlite::fromJSON(req$postBody)$instances

  # Convert input to tsibble
  # (Simulated logic: in a real HFT scenario, we'd do more preprocessing)
  # result <- model %>% forecast(h = 1)

  # Placeholder response for demo
  list(predictions = list(
    list(date = as.character(Sys.Date()), predicted_price = 2405.20)
  ))
}
