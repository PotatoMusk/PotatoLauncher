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


def check_rate_limits():
    """Check the bot's rate limits for key endpoints."""
    try:
        # Fetch rate limit status
        rate_limit_status = api.rate_limit_status()

        # Debug log for the full rate limit response
        logger.debug(f"Full rate limit status response: {rate_limit_status}")

        # Relevant endpoints
        tweet_posting_limits = rate_limit_status["resources"]["statuses"].get("/statuses/update", None)
        tweet_fetching_limits = rate_limit_status["resources"]["statuses"].get("/statuses/user_timeline", None)
        media_upload_limits = rate_limit_status["resources"]["media"].get("/media/upload", None)

        # Check for missing endpoints
        if not tweet_posting_limits:
            logger.warning("Could not retrieve rate limits for /statuses/update.")
            return False
        if not tweet_fetching_limits:
            logger.warning("Could not retrieve rate limits for /statuses/user_timeline.")
            return False
        if not media_upload_limits:
            logger.warning("Could not retrieve rate limits for /media/upload.")
            return False

        # Log the remaining limits
        logger.info(f"Tweet Posting: {tweet_posting_limits['remaining']} remaining. Resets at {time.ctime(tweet_posting_limits['reset'])}.")
        logger.info(f"Tweet Fetching: {tweet_fetching_limits['remaining']} remaining. Resets at {time.ctime(tweet_fetching_limits['reset'])}.")
        logger.info(f"Media Upload: {media_upload_limits['remaining']} remaining. Resets at {time.ctime(media_upload_limits['reset'])}.")

        # Check if any limits are hit
        if tweet_posting_limits["remaining"] == 0:
            logger.warning("Daily limit for posting tweets reached.")
            return False
        if tweet_fetching_limits["remaining"] == 0:
            logger.warning("Daily limit for fetching tweets reached.")
            return False
        if media_upload_limits["remaining"] == 0:
            logger.warning("Daily limit for media uploads reached.")
            return False

        return True  # All limits are within bounds
    except KeyError as e:
        logger.error(f"KeyError in rate limit status: {e}")
        return False
    except Exception as e:
        logger.error(f"Error checking rate limits: {e}")
        return False


def check_newest_tweet(user_id):
    """Fetch the newest tweet and process it if it's not a duplicate."""
    global last_tweet_id

    # Check rate limits before making the request
    if not check_rate_limits():
        logger.info("Rate limits reached. Skipping tweet check.")
        return

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
    except tweepy.TooManyRequests:
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
