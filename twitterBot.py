from dotenv.main import load_dotenv
import os
import tweepy
from dotenv import load_dotenv

load_dotenv()

consumer_key = os.getenv("CONSUMER_KEY")
consumer_secret = os.getenv("CONSUMER_SECRET")
access_token = os.getenv("ACCESS_TOKEN")
access_token_secret = os.getenv("ACCESS_TOKEN_SECRET")

# Authenticate to Twitter
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

# Create API object
api = tweepy.API(auth)

def tweet_station_congested(station, probability):
    api.update_status(f"VR trains going through {station} are going to be late with a probability of {int(probability * 100)}% #joukkoliikenne #VR")

if __name__ == '__main__':
    print(access_token)