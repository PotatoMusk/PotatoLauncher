import os
import tweepy
import time
import logging
import warnings

# Suppress SyntaxWarnings to avoid cluttering logs
warnings.filterwarnings("ignore", category=SyntaxWarning)

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load credentials from environment variables
credentials = {
    "BEARER_TOKEN": os.getenv("BEARER_TOKEN"),
    "API_KEY": os.getenv("API_KEY"),
    "API_SECRET": os.getenv("API_SECRET"),
    "ACCESS_TOKEN": os.getenv("ACCESS_TOKEN"),
    "ACCESS_SECRET": os.getenv("ACCESS_SECRET"),
}

# Authenticate with Twitter API using OAuth 2.0
client = tweepy.Client(
    bearer_token=credentials["BEARER_TOKEN"],
    consumer_key=credentials["API_KEY"],
    consumer_secret=credentials["API_SECRET"],
    access_token=credentials["ACCESS_TOKEN"],
    access_token_secret=credentials["ACCESS_SECRET"]
)

# User to monitor
target_username = "elonmusk"  # Replace with target user's handle (no '@')

# Keep track of the last tweet replied to
last_tweet_id = None

def get_user_id(username):
    """Fetch the user ID of the target username."""
    try:
        user = client.get_user(username=username)
        logger.info(f"Found user: {username}, ID: {user.data.id}")
        return user.data.id
    except tweepy.errors.TweepyException as e:
        logger.error(f"Error fetching user ID: {e}")
        if hasattr(e, 'response'):
            logger.error(f"API Response: {e.response.json()}")
        return None

def check_newest_tweet(user_id):
    """Fetch the newest tweet and process it if it's not a duplicate."""
    global last_tweet_id

    try:
        # Fetch up to 5 tweets from the target user
        tweets = client.get_users_tweets(
            id=user_id,
            max_results=5,
            tweet_fields=["id", "text", "created_at"],
            exclude=["replies", "retweets"]
        )

        if tweets and tweets.data:
            # Sort tweets by creation time to ensure the newest is processed
            sorted_tweets = sorted(tweets.data, key=lambda x: x.created_at, reverse=True)

            for tweet in sorted_tweets:
                # Skip if the tweet was already processed
                if tweet.id == last_tweet_id:
                    logger.info("No new tweet to process.")
                    return

                logger.info(f"Processing newest tweet ID {tweet.id}: {tweet.text}")

                # Post a reply to the tweet
                try:
                    response = client.create_tweet(
                        text="Elon Musk is a potato! #PotatoMusk  @potato_musk",
                        in_reply_to_tweet_id=tweet.id
                    )
                    logger.info(f"Replied to Tweet ID {tweet.id} with Reply ID {response.data['id']}")

                    # Retweet the bot's own reply
                    client.retweet(response.data['id'])
                    logger.info(f"Retweeted Reply ID {response.data['id']}")

                    # Update the last_tweet_id to the original tweet ID
                    last_tweet_id = tweet.id
                    break  # Process only the newest tweet

                except tweepy.errors.Forbidden as e:
                    logger.error(f"Tweet not allowed (403): {e}")
                except tweepy.errors.TweepyException as e:
                    logger.error(f"Error sending reply or retweeting: {e}")
    except tweepy.errors.TooManyRequests as e:
        logger.error("Rate limit hit. Sleeping for 24 hours...")
        time.sleep(24 * 60 * 60)  # 24 hours in seconds
    except tweepy.errors.TweepyException as e:
        logger.error(f"Error fetching tweets: {e}")

def run_bot():
    """Continuously monitor and reply to tweets."""
    logger.info("Bot started.")

    # Fetch the user ID
    user_id = get_user_id(target_username)
    logger.info(f"User ID retrieval result: {user_id}")  # Log the result for debugging
    if not user_id:
        logger.error("User ID could not be retrieved.")
        return

    logger.info("Entering main loop")
    # Main loop
    while True:
        try:
            check_newest_tweet(user_id)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        finally:
            # Wait for 24 hours between checks
            logger.info("Sleeping for 24 hours")
            time.sleep(24 * 60 * 60)  # 24 hours in seconds

if __name__ == "__main__":
    run_bot()
