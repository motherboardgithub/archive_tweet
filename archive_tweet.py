print "[*] Booting archive_tweet.py..."

import tweepy
import time
import sys
import json
import codecs
import random
import requests
import archiveis

from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream

# authentication pieces; put Twitter API keys here
client_key    = ""
client_secret = ""
token         = ""
token_secret  = ""

# feed authentication pieces into tweepy
auth = tweepy.OAuthHandler(client_key,client_secret)
auth.set_access_token(token,token_secret)
api = tweepy.API(auth)

#
# function for pushing to The Internet Archive/Wayback Machine
#
def internet_archive(tweet_to_archive):
    
    print "[*] Pushing to the Wayback Machine..."
    
    save_url = "https://web.archive.org/save/%s" % tweet_to_archive
    
    # send off request to wayback machine
    response = requests.get(save_url)
    
    if response.status_code == 200:
        
        # grab the part of the URL dealing with the archive page
        result               = response.headers['Content-Location']
        
        # build archive URL 
        internet_archive_url = "https://web.archive.org%s" % result
        
        return internet_archive_url
    else:
        print "[!] Internet Archive connection error"

# streaming API
class StdOutListener(StreamListener):
    
    def on_data(self, data):
        
        # convert from JSON to a dictionary
        tweet = json.loads(data)
        
        # grab the tweet's screen name, ID, etc
        tweet_id     = tweet.get('id_str')
        screen_name  = tweet.get('user',{}).get('screen_name')
        tweet_text   = tweet.get('text')
        
        # grab the reply tweet information
        reply_tweet_id          = tweet.get('in_reply_to_status_id_str')
        reply_tweet_screen_name = tweet.get('in_reply_to_screen_name')
        
        # make the URL of the tweet to archive
        tweet_to_archive = "https://twitter.com/%s/status/%s" % (reply_tweet_screen_name, reply_tweet_id)
        
        # print confirmation of finding tweet
        print "[*] Given tweet to archive: %s" % tweet_to_archive
        
        # archive the tweet
        internet_archive_url = internet_archive(tweet_to_archive)
        
        # push to archive.is
        print "[*] Pushing to archive.is..."
        archiveis_result = archiveis.capture(tweet_to_archive).replace("http://", "https://")        
        
        print "[!] Archived %s" % tweet_to_archive
        print internet_archive_url
        print archiveis_result
            
        # sleep, so the bot doesn't immediately reply and potentially trigger bot alerts
        time.sleep(10)

        # content of tweet to send to requester
        message = "Hey @%s, sure thing, here are the archive links: %s, %s" % (screen_name,internet_archive_url,archiveis_result)
        
        # post a reply to the tweet
        api.update_status(message,tweet_id)
        print "[!] Posted a reply"
              
        # sleep to avoid rate limiting
        time.sleep(300)
        
        return True
    
    def on_error(self, status):
        print "[!] ERROR: %s" % status
        
# listener
l = StdOutListener()
auth = OAuthHandler(client_key, client_secret)
auth.set_access_token(token, token_secret)

stream = Stream(auth, l)
stream.filter(track=['@archive_tweet'])
