import os
import tweepy
import json
import time
import logging

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load API credentials from JSON file
with open("config.json", "r") as file:
    credentials = json.load(file)

# Authenticate with Twitter API using OAuth 1.0a for media upload
auth = tweepy.OAuth1UserHandler(
    consumer_key=credentials["API_KEY"],
    consumer_secret=credentials["API_SECRET"],
    access_token=credentials["ACCESS_TOKEN"],
    access_token_secret=credentials["ACCESS_SECRET"]
)
api = tweepy.API(auth)  # For media uploads

# Authenticate with Twitter API using Client for tweet posting
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
    except Exception as e:
        logger.error(f"Error fetching user ID: {e}")
        return None


def check_newest_tweet(user_id):
    """Fetch the newest tweet and process it if it's not a duplicate."""
    global last_tweet_id

    try:
        # Fetch the newest tweet (latest by time)
        tweets = client.get_users_tweets(
            id=user_id,
            max_results=5,  # Fetch only the newest tweet
            tweet_fields=["id", "text", "created_at"],
            exclude=["replies", "retweets"]  # Exclude replies and retweets
        )

        if tweets and tweets.data:
            newest_tweet = tweets.data[0]  # Get the newest tweet
            if newest_tweet.id == last_tweet_id:
                logger.info("No new tweet to process.")
                return

            logger.info(f"Processing newest tweet ID {newest_tweet.id}: {newest_tweet.text}")
            try:
                # Path to your image in the root directory
                image_path = os.path.join(os.getcwd(), "potatoman.png")  # Replace with your image filename

                # Upload the image
                media = api.media_upload(image_path)
                logger.info(f"Image uploaded with Media ID: {media.media_id_string}")

                # Post a reply to the tweet with the image
                response = client.create_tweet(
                    text="Elon Musk is a FUCKING potato #PotatoMusk",  # Customize your reply text
                    in_reply_to_tweet_id=newest_tweet.id,
                    media_ids=[media.media_id_string]  # Attach the uploaded image
                )
                logger.info(f"Replied to Tweet ID {newest_tweet.id} with Reply ID {response.data['id']}")

                # Update the last_tweet_id to prevent duplication
                last_tweet_id = newest_tweet.id

            except Exception as e:
                logger.error(f"Error sending reply: {e}")
    except tweepy.TooManyRequests as e:
        logger.error("Rate limit hit. Waiting 15 minutes...")
        time.sleep(15 * 60)  # Wait 15 minutes
    except Exception as e:
        logger.error(f"Error fetching tweets: {e}")


def run_bot():
    """Continuously monitor and reply to tweets."""
    logger.info("Bot started.")
    user_id = get_user_id(target_username)
    if not user_id:
        logger.error("User ID could not be retrieved.")
        return

    while True:
        try:
            check_newest_tweet(user_id)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        finally:
            # Wait for 30 minutes (or adjust dynamically)
            time.sleep(30 * 60)


if __name__ == "__main__":
    run_bot()
