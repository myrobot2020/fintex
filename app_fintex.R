library(shiny)
library(httr)
library(jsonlite)
library(ggplot2)
library(dplyr)
library(lubridate)
library(plotly)

# CONFIG
API_URL <- "https://gold-forecast-api-jayxrndnrq-uc.a.run.app/forecast"

ui <- fluidPage(
  tags$head(
    tags$style(HTML('body {background-color: #121212; color: white;}')),
    tags$style(HTML('.well {background-color: #1e1e1e; border: none;}')),
    tags$style(HTML('.btn-primary {background-color: #f39c12; border: none;}'))
  ),

  titlePanel(span("💰 Fintex: Gold Price Intelligence", style="color: #f39c12;")),

  sidebarLayout(
    sidebarPanel(
      h4("Control Panel"),
      sliderInput("horizon", "Forecast Horizon (Days):", min = 1, max = 14, value = 7),
      actionButton("refresh", "Fetch Live Forecast", class = "btn-primary"),
      hr(),
      wellPanel(
        h5("Model Status"),
        p(strong("Champion:"), "XGBoost (Pipeline)"),
        p(strong("Challenger:"), "ARIMA (Online)"),
        p(strong("Status:"), span("Cost-Safe (Cold)", style="color: #2ecc71;"))
      )
    ),

    mainPanel(
      tabsetPanel(
        tabPanel("Live Forecast",
                 br(),
                 plotlyOutput("forecast_plot", height = "500px"),
                 br(),
                 tableOutput("forecast_table")),
        tabPanel("Tournament Stats",
                 br(),
                 h4("Global MAE Leaderboard"),
                 tableOutput("leaderboard"))
      )
    )
  )
)

server <- function(input, output, session) {

  # Fetch data from Cloud Run API
  forecast_data <- eventReactive(input$refresh, {
    req <- GET(paste0(API_URL, "?horizon=", input$horizon))
    if (status_code(req) == 200) {
      data <- fromJSON(content(req, "text"))
      df <- as.data.frame(data$forecasts)
      df$date <- as.Date(df$date)
      return(df)
    } else {
      return(NULL)
    }
  }, ignoreNULL = FALSE)

  # Forecast Plot
  output$forecast_plot <- renderPlotly({
    df <- forecast_data()
    if (is.null(df)) return(NULL)

    p <- ggplot(df, aes(x = date, y = predicted_price)) +
      geom_line(color = "#f39c12", size = 1) +
      geom_point(color = "#f39c12", size = 3) +
      geom_ribbon(aes(ymin = lower_bound, ymax = upper_bound), fill = "#f39c12", alpha = 0.2) +
      theme_minimal() +
      labs(title = "14-Day Gold Price Outlook (ARIMA Challenger)",
           x = "Date", y = "Price (USD)") +
      theme(text = element_text(color = "white"),
            panel.grid = element_line(color = "#333"))

    ggplotly(p)
  })

  # Forecast Table
  output$forecast_table <- renderTable({
    df <- forecast_data()
    if (!is.null(df)) {
      df %>% select(date, predicted_price, lower_bound, upper_bound)
    }
  })

  # Mock Leaderboard (from our Experiment)
  output$leaderboard <- renderTable({
    data.frame(
      Rank = c("🥇 1st", "🥈 2nd", "🥉 3rd"),
      Model = c("R-GARCH v4", "Ensemble v2", "XGBoost Local"),
      MAE = c(39.12, 45.12, 46.79),
      Technology = c("R (rugarch)", "Python (Voting)", "XGBoost")
    )
  })
}

shinyApp(ui, server)
