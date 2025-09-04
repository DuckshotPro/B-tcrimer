
import os
import requests
import tweepy
import random

# --- Configuration ---

# TODO: Replace with your actual B-TCrimer API endpoint
B_TCRIMER_API_URL = "https://api.b-tcrimer.com/v1/market/insights" 

# It's best practice to use environment variables for secrets.
# The script will look for these variables in your environment.
# Example: export TWITTER_API_KEY="your_key_here"
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")


def get_market_insight():
    """
    Fetches market data from the B-TCrimer API and finds an interesting insight.
    
    NOTE: This function currently uses MOCK DATA. You should replace this
    with a real API call and logic to find a truly interesting metric.
    """
    print("Fetching market data...")
    # try:
    #     # TODO: Add authentication if your API requires it
    #     response = requests.get(B_TCRIMER_API_URL, timeout=15)
    #     response.raise_for_status()  # Raises an HTTPError for bad responses
    #     data = response.json()
    # except requests.exceptions.RequestException as e:
    #     print(f"Error fetching data from B-TCrimer API: {e}")
    #     return None

    # --- MOCK DATA BLOCK ---
    # Replace this block with your actual API call and analysis logic
    mock_data = {
        "volatility": {
            "asset": "Bitcoin",
            "symbol": "BTC",
            "value": round(random.uniform(0.5, 3.5), 2),
            "change": round(random.uniform(-0.5, 0.5), 2),
            "period": "24h"
        },
        "top_mover": {
            "asset": "Cardano",
            "symbol": "ADA",
            "change_pct": round(random.uniform(5, 25), 1),
            "direction": "up"
        },
        "volume_spike": {
            "asset": "Solana",
            "symbol": "SOL",
            "increase_pct": random.randint(50, 300)
        }
    }
    insight_type = random.choice(list(mock_data.keys()))
    insight = mock_data[insight_type]
    insight['type'] = insight_type
    # --- END MOCK DATA BLOCK ---
    
    print(f"Found insight: {insight}")
    return insight


def format_post(insight):
    """Formats the insight data into a Twitter-ready post."""
    post_text = ""
    if insight['type'] == 'volatility':
        post_text = (
            f"📈 Market Insight: #{insight['asset']} volatility is currently at {insight['value']}%.\n\n"
            f"Sharp moves could be on the horizon. #BTC #CryptoData"
        )
    elif insight['type'] == 'top_mover':
        post_text = (
            f"🚀 Top Mover: #{insight['asset']} is up {insight['change_pct']}% in the last 24 hours!\n\n"
            f"#{insight['symbol']} is making waves today. #Altcoins #Crypto"
        )
    elif insight['type'] == 'volume_spike':
        post_text = (
            f"📊 Volume Alert: Trading volume for #{insight['asset']} has spiked by {insight['increase_pct']}%.\n\n"
            f"Increased activity suggests growing interest. #{insight['symbol']} #Trading"
        )
    
    # Add a consistent closing
    post_text += "\n\n(Data via the B-TCrimer API)"
    return post_text


def post_to_twitter(text):
    """Authenticates with the Twitter API and posts the given text."""
    if not all([TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET]):
        print("\n--- ERROR ---")
        print("Twitter API credentials are not configured.")
        print("Please set the following environment variables:")
        print("  - TWITTER_API_KEY")
        print("  - TWITTER_API_SECRET")
        print("  - TWITTER_ACCESS_TOKEN")
        print("  - TWITTER_ACCESS_TOKEN_SECRET")
        print("--------------------\n")
        return False

    try:
        # Using v2 of the Twitter API
        client = tweepy.Client(
            consumer_key=TWITTER_API_KEY,
            consumer_secret=TWITTER_API_SECRET,
            access_token=TWITTER_ACCESS_TOKEN,
            access_token_secret=TWITTER_ACCESS_TOKEN_SECRET
        )
        print("Authenticated with Twitter successfully.")
        
        client.create_tweet(text=text)
        print(f"Successfully posted to Twitter:\n---\n{text}\n---")
        return True
    except Exception as e:
        print(f"An error occurred while posting to Twitter: {e}")
        return False


def main():
    """Main function to run the social poster bot."""
    print("--- Starting Social Media Poster Script ---")
    insight = get_market_insight()
    
    if not insight:
        print("Could not retrieve a market insight. Exiting.")
        return
        
    post_text = format_post(insight)
    
    if not post_text:
        print("Could not format a post from the insight. Exiting.")
        return
        
    post_to_twitter(post_text)
    print("--- Script Finished ---")


if __name__ == "__main__":
    main()
