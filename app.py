import tweepy
import time
import json

# Load credentials from JSON file
with open("credentials.json", "r") as file:
    creds = json.load(file)

# Use the credentials
API_KEY = creds["API_KEY"]
API_SECRET = creds["API_SECRET"]
ACCESS_TOKEN = creds["ACCESS_TOKEN"]
ACCESS_SECRET = creds["ACCESS_SECRET"]

# Authenticate with Twitter
auth = tweepy.OAuthHandler(API_KEY, API_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)
api = tweepy.API(auth)

print("Authentication successful!")

# Define the target tweet and the reply message
target_user = "ABitoftheUltra1"  # Replace with the user's handle (without @)
original_tweet_id = "1868773813363884161"  # Replace with the ID of the target tweet
reply_message = "Elon Musk is a fucking potato #PotatoMusk"

# Fetch replies to the original tweet
def fetch_replies(tweet_id, username):
    search_query = f"to:{username}"  # Search for tweets directed at the user
    replies = []
    try:
        for tweet in tweepy.Cursor(api.search_tweets, q=search_query, since_id=tweet_id, tweet_mode='extended').items():
            if tweet.in_reply_to_status_id == int(tweet_id):  # Check if it's a reply to the original tweet
                replies.append(tweet)
    except tweepy.TweepError as e:
        print(f"Error fetching replies: {e}")
    return replies

# Post a reply to each reply
def reply_to_replies():
    replies = fetch_replies(original_tweet_id, target_user)
    for reply in replies:
        try:
            api.update_status(
                status=f"@{reply.user.screen_name} {reply_message}",
                in_reply_to_status_id=reply.id
            )
            print(f"Replied to @{reply.user.screen_name}")
            time.sleep(5)  # Add delay to avoid spam filters
        except tweepy.TweepError as e:
            print(f"Error replying to @{reply.user.screen_name}: {e}")

# Run the bot
reply_to_replies()