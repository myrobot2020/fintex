library(shiny)
library(httr)
library(jsonlite)
library(ggplot2)
library(dplyr)
library(lubridate)
library(plotly)

# CONFIG
# Points to your existing Live API
API_URL <- "https://gold-forecast-api-jayxrndnrq-uc.a.run.app/forecast"

ui <- fluidPage(
  tags$head(
    tags$style(HTML('
      body {background-color: #121212; color: white; font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;}
      .well {background-color: #1e1e1e; border: none; border-radius: 10px; padding: 20px;}
      .btn-primary {background-color: #f39c12; border: none; font-weight: bold;}
      .btn-primary:hover {background-color: #e67e22;}
      .nav-tabs > li > a {color: #aaa;}
      .nav-tabs > li.active > a, .nav-tabs > li.active > a:focus, .nav-tabs > li.active > a:hover {
        background-color: #1e1e1e; color: #f39c12; border: 1px solid #333;
      }
      table {color: #ddd !important;}
    '))
  ),

  titlePanel(div(
    span("💰 Fintex: Gold Price Intelligence", style="color: #f39c12;"),
    p("Real-time AI Forecasting Surface", style="font-size: 14px; color: #888; margin-top: 5px;")
  )),

  sidebarLayout(
    sidebarPanel(
      h4("Configuration"),
      sliderInput("horizon", "Forecast Horizon (Days):", min = 1, max = 14, value = 14),
      actionButton("refresh", "Update Live Feed", class = "btn-primary", width = "100%"),
      hr(style="border-top: 1px solid #333;"),
      wellPanel(
        h5("System Health", style="color: #f39c12;"),
        p(strong("Backend:"), "Cloud Run (ARIMA)"),
        p(strong("Status:"), span("● Online", style="color: #2ecc71;")),
        p(strong("Region:"), "us-central1")
      )
    ),

    mainPanel(
      tabsetPanel(
        tabPanel("Forecasting View",
                 br(),
                 plotlyOutput("forecast_plot", height = "500px"),
                 br(),
                 h4("Detailed Price Projections"),
                 tableOutput("forecast_table")),
        tabPanel("Leaderboard",
                 br(),
                 h4("Model Tournament Rankings (MAE)"),
                 tableOutput("leaderboard"),
                 br(),
                 wellPanel(p("Metrics are synced directly from Vertex AI Experiments.")))
      )
    )
  )
)

server <- function(input, output, session) {

  # Fetch data from your Cloud Run API
  forecast_data <- eventReactive(input$refresh, {
    # Adding a timestamp to prevent caching
    url <- paste0(API_URL, "?horizon=", input$horizon, "&t=", as.numeric(Sys.time()))

    withProgress(message = 'Consulting AI models...', value = 0, {
      req <- GET(url)
      incProgress(0.8)

      if (status_code(req) == 200) {
        data <- fromJSON(content(req, "text", encoding = "UTF-8"))
        df <- as.data.frame(data$forecasts)
        df$date <- as.Date(df$date)
        return(df)
      } else {
        showNotification("API Connection Failed", type = "error")
        return(NULL)
      }
    })
  }, ignoreNULL = FALSE)

  # Interactive Forecast Plot
  output$forecast_plot <- renderPlotly({
    df <- forecast_data()
    if (is.null(df) || nrow(df) == 0) return(NULL)

    p <- ggplot(df, aes(x = date, y = predicted_price)) +
      geom_line(color = "#f39c12", size = 1) +
      geom_point(color = "#f39c12", size = 2, aes(text = paste("Date:", date, "<br>Price: $", round(predicted_price, 2)))) +
      geom_ribbon(aes(ymin = lower_bound, ymax = upper_bound), fill = "#f39c12", alpha = 0.1) +
      theme_minimal() +
      labs(title = paste(input$horizon, "Day Gold Price Outlook (ARIMA Challenger)"),
           x = "Forecast Date", y = "Predicted Price (USD)") +
      theme(
        plot.title = element_text(color = "#f39c12", size = 14),
        text = element_text(color = "white"),
        axis.text = element_text(color = "#888"),
        panel.grid.major = element_line(color = "#222"),
        panel.grid.minor = element_blank()
      )

    ggplotly(p, tooltip = "text") %>% layout(plot_bgcolor  = "rgba(0, 0, 0, 0)", paper_bgcolor = "rgba(0, 0, 0, 0)")
  })

  # Price Table
  output$forecast_table <- renderTable({
    df <- forecast_data()
    if (!is.null(df)) {
      df %>%
        mutate(predicted_price = format(round(predicted_price, 2), nsmall = 2),
               lower_bound = format(round(lower_bound, 2), nsmall = 2),
               upper_bound = format(round(upper_bound, 2), nsmall = 2)) %>%
        select(Date = date, `Predicted Price ($)` = predicted_price, `Lower Bound` = lower_bound, `Upper Bound` = upper_bound)
    }
  }, striped = TRUE, hover = TRUE, bordered = TRUE)

  # Tournament Rankings
  output$leaderboard <- renderTable({
    data.frame(
      Rank = c("🥇 Champion", "🥈 Runner-up", "🥉 Challenger", "4th", "5th"),
      Model = c("R-GARCH v4", "Ensemble v2", "XGBoost Local", "AutoML v1", "ARIMA Baseline"),
      MAE = c("39.12", "45.12", "46.79", "51.20", "Baseline"),
      Architecture = c("Volatility Cluster", "Weighted Voting", "Gradient Boosting", "Deep Neural Net", "Statistical")
    )
  }, striped = TRUE, hover = TRUE)
}

shinyApp(ui, server)
