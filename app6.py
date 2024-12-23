import os
import tweepy
import json
import time
import logging

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load API credentials from JSON file
with open("credentials.json", "r") as file:
    credentials = json.load(file)

# Authenticate with Twitter API using Client
client = tweepy.Client(
    bearer_token=credentials["BEARER_TOKEN"],
    consumer_key=credentials["API_KEY"],
    consumer_secret=credentials["API_SECRET"],
    access_token=credentials["ACCESS_TOKEN"],
    access_token_secret=credentials["ACCESS_SECRET"]
)

# User to monitor
target_username = "elonmusk"  # Replace with target user's handle (no '@')
LAST_TWEET_FILE = "last_tweet_id.txt"

def load_last_tweet_id():
    """Load the last tweet ID from a file."""
    if os.path.exists(LAST_TWEET_FILE):
        with open(LAST_TWEET_FILE, "r") as file:
            return file.read().strip()
    return None

def save_last_tweet_id(tweet_id):
    """Save the last tweet ID to a file."""
    with open(LAST_TWEET_FILE, "w") as file:
        file.write(tweet_id)

def fetch_user_id(username):
    """Fetch the user ID of the target username."""
    try:
        user = client.get_user(username=username)
        logger.info(f"Found user: {username}, ID: {user.data.id}")
        return user.data.id
    except Exception as e:
        logger.error(f"Error fetching user ID: {e}")
        return None

def check_newest_tweet(user_id):
    """Fetch the newest tweet and process it if it's not a duplicate."""
    global last_tweet_id
    last_tweet_id = load_last_tweet_id()

    try:
        tweets = client.get_users_tweets(
            id=user_id,
            max_results=5,
            tweet_fields=["id", "text", "created_at"],
            exclude=["retweets"]
        )

        if tweets is None or tweets.data is None or len(tweets.data) == 0:
            logger.info("No tweets found.")
            return

        newest_tweet = tweets.data[0]
        if newest_tweet.id == last_tweet_id:
            logger.info("No new tweet to process.")
            return

        logger.info(f"Processing newest tweet ID {newest_tweet.id}: {newest_tweet.text}")

        # Post a reply to the tweet
        reply_text = "Elon Musk is a FUCKING potato #PotatoMusk"
        response = client.create_tweet(
            text=reply_text,
            in_reply_to_tweet_id=newest_tweet.id
        )
        logger.info(f"Replied to Tweet ID {newest_tweet.id} with Reply ID {response.data['id']}")

        # Save the last tweet ID
        save_last_tweet_id(newest_tweet.id)

    except tweepy.errors.TooManyRequests:
        handle_rate_limit()
    except Exception as e:
        logger.error(f"Error fetching or replying to tweets: {e}")

def handle_rate_limit():
    """Handle rate limit by sleeping until the reset time."""
    reset_time = int(time.time()) + 15 * 60  # Default 15 minutes
    try:
        reset_time = int(client.rate_limit_status()["x-rate-limit-reset"])
    except Exception as e:
        logger.warning(f"Could not fetch rate limit reset time: {e}")
    wait_time = reset_time - int(time.time())
    logger.warning(f"Rate limit hit. Waiting {wait_time} seconds...")
    time.sleep(max(wait_time, 60))

def run_bot():
    """Continuously monitor and reply to tweets."""
    logger.info("Bot started.")
    user_id = fetch_user_id(target_username)
    if not user_id:
        logger.error("User ID could not be retrieved. Exiting.")
        return

    while True:
        try:
            check_newest_tweet(user_id)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        finally:
            time.sleep(432 * 60) # 7 hours and 12 minutes between requests

if __name__ == "__main__":
    run_bot()
