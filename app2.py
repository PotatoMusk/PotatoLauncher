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
    except tweepy.TooManyRequests as e:
        logger.error(f"Rate limit hit: {e}")
        logger.info("Waiting 15 minutes before retrying...")
        time.sleep(16 * 60)  # Wait 16 minutes (rate limit reset)
        return get_user_id(username)
    except Exception as e:
        logger.error(f"Error fetching user ID: {e}")
        return None

def check_new_posts(user_id):
    """Check for the latest original post and reply to it."""
    global last_tweet_id

    try:
        # Fetch up to 5 recent tweets (minimum valid value for max_results)
        tweets = client.get_users_tweets(
            id=user_id,
            since_id=last_tweet_id,
            max_results=5,  # Minimum value allowed by the API
            tweet_fields=["id", "text", "created_at"],
            exclude=["replies", "retweets"]  # Exclude replies and retweets
        )

        # Process only the first (latest) tweet
        if tweets and tweets.data:
            tweet = tweets.data[0]  # Take the first tweet
            logger.info(f"Replying to Tweet ID {tweet.id}: {tweet.text}")
            try:
                # Path to your image in the root directory
                image_path = os.path.join(os.getcwd(), "potatoman.png")  # Replace with your image filename

                # Upload the image
                media = api.media_upload(image_path)
                logger.info(f"Image uploaded with Media ID: {media.media_id_string}")

                # Post a reply to the tweet with the image
                response = client.create_tweet(
                    text="Elon Musk is a FUCKING potato #PotatoMusk",  # Customize your reply text
                    in_reply_to_tweet_id=tweet.id,
                    media_ids=[media.media_id_string]  # Attach the uploaded image
                )
                logger.info(f"Replied to Tweet ID {tweet.id} with Reply ID {response.data['id']}")
                last_tweet_id = tweet.id  # Update last replied tweet ID

                # Generate the link to the reply tweet
                reply_tweet_link = f"https://twitter.com/{target_username}/status/{response.data['id']}"

                # Create the confirmation tweet with the link to the reply tweet
                confirmation_tweet = client.create_tweet(
                    text=f"Elon Musk is a FUCKING potato! #PotatoMusk Check it out: {reply_tweet_link}"
                )
                logger.info(f"Confirmation tweet posted with ID {confirmation_tweet.data['id']}")

            except Exception as e:
                logger.error(f"Error sending reply: {e}")
    except tweepy.TooManyRequests:
        logger.error("Rate limit reached. Backing off...")
        time.sleep(16 * 60)  # Wait 16 minutes (rate limit reset)
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
        check_new_posts(user_id)
        time.sleep(30 * 60)  # Check every 30 minutes

if __name__ == "__main__":
    run_bot()
