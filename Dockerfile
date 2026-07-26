# Use official R Shiny image
FROM rocker/shiny:4.3.0

# Install system dependencies for R packages
RUN apt-get update && apt-get install -y \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    && rm -rf /var/lib/apt/lists/*

# Install necessary R packages
RUN R -e "install.packages(c('shiny', 'httr', 'jsonlite', 'ggplot2', 'dplyr', 'lubridate', 'plotly'), repos='https://cloud.r-project.org/')"

# Set working directory
WORKDIR /app

# Copy the app file (must be named app.R for rocker/shiny)
COPY app_fintex.R /app/app.R

# Cloud Run uses port 8080 by default
EXPOSE 8080

# Start the Shiny app on 0.0.0.0:8080
CMD ["R", "-e", "shiny::runApp('/app', host='0.0.0.0', port=8080)"]
