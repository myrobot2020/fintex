library(shiny)
library(ggplot2)
library(dplyr)
library(lubridate)
library(plotly)
library(readr)
library(tidyr)

# CONFIG
DATA_PATH <- "C:/Users/ADMIN/Desktop/cl/finance/gold_consensus_raw.csv"

ui <- fluidPage(
  tags$head(
    tags$style(HTML('
      body {background-color: #0f111a; color: #e0e0e0; font-family: "Courier New", Courier, monospace;}
      .well {background-color: #1a1c27; border: 1px solid #333;}
      .btn-primary {background-color: #00ff41; color: black; border: none; font-weight: bold;}
      .btn-primary:hover {background-color: #00cc33;}
    '))
  ),

  titlePanel(span("⚡ Fintex: Multi-Source Tick Viewer", style="color: #00ff41;")),

  sidebarLayout(
    sidebarPanel(
      width = 3,
      h4("Stream Control"),
      checkboxInput("auto_refresh", "Enable Live Polling", value = TRUE),
      sliderInput("n_ticks", "Ticks to Display:", min = 10, max = 200, value = 50),
      hr(),
      wellPanel(
        h5("Consensus Logic", style="color: #00ff41;"),
        p("1. Fetch GC=F (Futures)"),
        p("2. Fetch GLD (ETF)"),
        p("3. Normalize Parity"),
        p("4. Average Weighting")
      )
    ),

    mainPanel(
      width = 9,
      tabsetPanel(
        tabPanel("Tick Chart",
                 br(),
                 plotlyOutput("tick_plot", height = "500px")),
        tabPanel("Raw Consensus Data",
                 br(),
                 tableOutput("raw_table"))
      )
    )
  )
)

server <- function(input, output, session) {

  # Reactive timer for "Live" simulation (every 3 seconds)
  auto_timer <- reactiveTimer(3000)

  # Load and Process Data
  current_data <- reactive({
    if(input$auto_refresh) auto_timer()

    if(!file.exists(DATA_PATH)) {
      showNotification("Data source not found. Run multi_horizon_data.py", type="error")
      return(NULL)
    }

    df <- read_csv(DATA_PATH, show_col_types = FALSE) %>%
      mutate(timestamp = as.POSIXct(timestamp)) %>%
      arrange(desc(timestamp)) %>%
      head(input$n_ticks)

    return(df)
  })

  # Visualization
  output$tick_plot <- renderPlotly({
    df <- current_data()
    if(is.null(df) || nrow(df) == 0) return(NULL)

    # Pivot for plotting multiple sources
    df_long <- df %>%
      select(timestamp, `GC=F`, consensus_price) %>%
      pivot_longer(cols = -timestamp, names_to = "Source", values_to = "Price")

    p <- ggplot(df_long, aes(x = timestamp, y = Price, color = Source)) +
      geom_line(size = 0.8) +
      geom_point(size = 1.5) +
      scale_color_manual(values = c("GC=F" = "#555", "consensus_price" = "#00ff41")) +
      theme_minimal() +
      labs(title = "Gold Price Consensus: Raw vs Smoothed", x = "Tick Time", y = "Price (USD)") +
      theme(
        plot.background = element_rect(fill = "#0f111a"),
        panel.background = element_rect(fill = "#0f111a"),
        text = element_text(color = "white"),
        panel.grid = element_line(color = "#222"),
        legend.position = "bottom"
      )

    ggplotly(p) %>% layout(plot_bgcolor  = "rgba(0, 0, 0, 0)", paper_bgcolor = "rgba(0, 0, 0, 0)")
  })

  output$raw_table <- renderTable({
    current_data() %>%
      mutate(timestamp = as.character(timestamp))
  })
}

shinyApp(ui, server)
