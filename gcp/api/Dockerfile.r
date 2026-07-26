# Production R Container for Vertex AI Prediction
FROM rocker/r-ver:4.3.0

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    && rm -rf /var/lib/apt/lists/*

# Install R packages
RUN R -e "install.packages(c('plumber', 'jsonlite', 'fable', 'tsibble', 'dplyr', 'lubridate', 'readr'))"

# Copy API and model
WORKDIR /app
COPY r_challenger_plumber.R /app/plumber.R
# COPY gold_ensemble_model.rds /app/gold_ensemble_model.rds

# Vertex AI expects port 8080
EXPOSE 8080

# Start Plumber
CMD ["R", "-e", "pr <- plumber::plumb('/app/plumber.R'); pr$run(host='0.0.0.0', port=8080)"]
