import requests
import json

URL = "https://gold-forecast-api-jayxrndnrq-uc.a.run.app/forecast?horizon=14"

def show():
    try:
        r = requests.get(URL)
        data = r.json()

        print("\n💰 --- LIVE GOLD PROJECTED PRICES --- 💰")
        print(f"Generated at: {data['generated_at']}")
        print(f"Model Source: {data['model_source']}\n")

        print(f"{'Date':<12} | {'Price ($)':<12} | {'Range (95% CI)':<20}")
        print("-" * 50)

        for f in data['forecasts']:
            price = f"{f['predicted_price']:,.2f}"
            ci = f"[{f['lower_bound']:,.2f} - {f['upper_bound']:,.2f}]"
            print(f"{f['date']:<12} | {price:<12} | {ci}")

        print("\n🚀 UI Ready at: finance/app_fintex.R")
        print("To run locally: shiny::runApp('finance/app_fintex.R')")

    except Exception as e:
        print(f"Error fetching live data: {e}")

if __name__ == "__main__":
    show()
