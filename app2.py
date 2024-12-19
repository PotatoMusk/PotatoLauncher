import tweepy
import json
import time
# latest tweet reply

# Load API credentials from JSON file
with open("config.json", "r") as file:
    credentials = json.load(file)

# Authenticate with Twitter API using OAuth 1.0a for write access
client = tweepy.Client(
    bearer_token=credentials["BEARER_TOKEN"],
    consumer_key=credentials["API_KEY"],
    consumer_secret=credentials["API_SECRET"],
    access_token=credentials["ACCESS_TOKEN"],  # Updated access token
    access_token_secret=credentials["ACCESS_SECRET"]  # Updated access secret
)

# User to monitor
target_username = "elonmusk"  # Replace with target user's handle (no '@')

# Keep track of the last tweet replied to
last_tweet_id = None


def get_user_id(username):
    """Fetch the user ID of the target username."""
    try:
        user = client.get_user(username=username)
        print(f"Found user: {username}, ID: {user.data.id}")
        return user.data.id
    except tweepy.TooManyRequests as e:
        print(f"Rate limit hit: {e}")
        print("Waiting 2 hours before retrying...")
        time.sleep(2 * 60 * 60)  # Wait 2 hours (2 hours * 60 minutes/hour * 60 seconds/minute)
        return get_user_id(username)
    except Exception as e:
        print(f"Error fetching user ID: {e}")
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
            print(f"Replying to Tweet ID {tweet.id}: {tweet.text}")
            try:
                # Post a reply to the tweet
                response = client.create_tweet(
                    text="Elon Musk is a FUCKING potato #PotatoMusk",  # Customize your reply text
                    in_reply_to_tweet_id=tweet.id
                )
                print(f"Replied to Tweet ID {tweet.id} with Reply ID {response.data['id']}")
                last_tweet_id = tweet.id  # Update last replied tweet ID
            except Exception as e:
                print(f"Error sending reply: {e}")
    except Exception as e:
        print(f"Error fetching tweets: {e}")


# Main Execution
if __name__ == "__main__":
    user_id = None
    try:
        # Cache the user ID (fetch once)
        user_id = get_user_id(target_username)
        if user_id:
            print(f"Monitoring tweets for user ID {user_id}...")
            while True:
                check_new_posts(user_id)
                time.sleep(60)  # Check every 60 seconds
        else:
            print("Could not find the target user. Please check the username.")
    except KeyboardInterrupt:
        print("Script stopped manually.")
