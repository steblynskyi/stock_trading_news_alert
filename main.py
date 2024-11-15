import os
import requests
from twilio.rest import Client

# Constants
STOCK_NAME = "TSLA"
COMPANY_NAME = "Tesla Inc"

# AlphaVantage Setup
STOCK_ENDPOINT = "https://www.alphavantage.co/query"
ALPHA_VANTAGE_API_KEY = os.environ.get("ALPHA_VANTAGE_API_KEY")
if not ALPHA_VANTAGE_API_KEY:
    raise ValueError("AlphaVantage API key is missing!")

alpha_vantage_parameters = {
    "function": "TIME_SERIES_DAILY",
    "symbol": STOCK_NAME,
    "apikey": ALPHA_VANTAGE_API_KEY
}

# NewsApi Setup
NEWS_ENDPOINT = "https://newsapi.org/v2/everything"
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")
if not NEWS_API_KEY:
    raise ValueError("NewsAPI key is missing!")

news_parameters = {
    "qInTitle": COMPANY_NAME,
    "apiKey": NEWS_API_KEY
}

# Twilio Setup
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
    raise ValueError("Twilio credentials are missing!")

# Twilio phone numbers
TWILIO_VIRTUAL_NUMBER = os.environ.get("TWILIO_VIRTUAL_NUMBER")
TWILIO_VERIFIED_NUMBER = os.environ.get("TWILIO_VERIFIED_NUMBER")
if not TWILIO_VIRTUAL_NUMBER or not TWILIO_VERIFIED_NUMBER:
    raise ValueError("Twilio phone numbers are missing!")

# Get stock data
try:
    response = requests.get(STOCK_ENDPOINT, params=alpha_vantage_parameters)
    response.raise_for_status()
    data = response.json().get("Time Series (Daily)", {})
    if not data:
        raise ValueError("No stock data found.")

    # Extract stock prices
    data_list = list(data.values())
    yesterday_data = data_list[0]
    day_before_yesterday = data_list[1]

    yesterday_closing_price = float(yesterday_data["4. close"])
    day_before_yesterday_price = float(day_before_yesterday["4. close"])

    # Calculate price change
    difference = yesterday_closing_price - day_before_yesterday_price
    diff_percent = round((difference / yesterday_closing_price) * 100)

    # Determine if we need to send news
    if abs(diff_percent) > 5:
        # Get news articles
        news_response = requests.get(NEWS_ENDPOINT, params=news_parameters)
        news_response.raise_for_status()
        articles = news_response.json().get("articles", [])[:3]

        if articles:
            # Prepare message for each article
            formatted_articles = [
                f"{STOCK_NAME}: {'🔺' if difference > 0 else '🔻'}{diff_percent}% \nHeadline: {article['title']}. \nBrief: {article['description']}"
                for article in articles
            ]

            # Send messages using Twilio
            client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            for article in formatted_articles:
                message = client.messages.create(
                    from_=TWILIO_VIRTUAL_NUMBER,
                    to=TWILIO_VERIFIED_NUMBER,
                    body=article
                )
                print(f"Sent message with status: {message.status}")
        else:
            print("No relevant news articles found.")
    else:
        print(f"Stock change of {diff_percent}% is not significant enough to send news.")
except requests.exceptions.RequestException as e:
    print(f"Error with API requests: {e}")
except ValueError as e:
    print(f"Error: {e}")
