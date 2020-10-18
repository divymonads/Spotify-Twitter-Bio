import tweepy
import os
import requests
import time 
import boto3
import json

# Authenticate to Twitter
auth = tweepy.OAuthHandler(os.environ['TW_API_KEY'], os.environ['TW_API_SECRET'])
auth.set_access_token(os.environ['TW_ACCESS_TOKEN'], os.environ['TW_ACCESS_SECRET'])
twit_api = tweepy.API(auth)

# Connect DynamoDB database
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('SpotifyState')

# Initial Spotify Refresh Token
refreshToken = os.environ['INITIAL_SPOTIFY_REFRESH']

# Spotify Refresh Token Function
# Only called if the current accessToken is expired (on first visit after ~1hr)
def refreshTheToken(refreshToken):
    clientIdClientSecret = os.environ['SPOTIFY_CLIENT_ID_SECRET']
    data = {'grant_type': 'refresh_token', 'refresh_token': refreshToken}

    headers = {'Authorization': clientIdClientSecret}
    p = requests.post('https://accounts.spotify.com/api/token', data=data, headers=headers)

    spotifyToken = p.json()

    # Place the expiration time (current time + almost an hour), and access token into the DB
    table.put_item(Item={'spotify': 'prod', 'expiresAt': int(time.time()) + 3200,
                                        'accessToken': spotifyToken['access_token']})

# Calculate Bio Functionality
bio_add_on = " | 🎶 listening to " 

def getCurrBioAddOnIndex():
    currBio = twit_api.me()._json['description']
    return currBio.rfind(bio_add_on)

def getCurrBio():
    currBio = twit_api.me()._json['description']
    x = getCurrBioAddOnIndex()
    if x != -1:
        currBio = currBio[:x]
    return currBio

def getNewBio(currently_playing):
    bio_str = bio_add_on + currently_playing['item']['artists'][0]['name']
    currBio = getCurrBio()
    newBio = currBio + bio_str + " on spotify"
    return newBio


# Get Currently Playing
# Basic Idea for refresh token renewal copied from JoshSpicer.com
def makeRequest(accessToken):
    headers = {'Authorization': 'Bearer ' + accessToken,
                   'Content-Type': 'application/json', 'Accept': 'application/json'}
    r = requests.get('https://api.spotify.com/v1/me/player/currently-playing', headers=headers)

    isPlaying = False
    newBio = ''
    currBio = getCurrBio()
    try:
        r_json = r.json()
        isPlaying = r_json['is_playing']
        if isPlaying:
            newBio = getNewBio(r_json)
    except:
        pass
    return isPlaying, currBio, newBio 



# Main Lambda
def lambda_handler(event, context):
    # Check Functionality for Twitter
    try: 
        twit_api.verify_credentials()
        print("Twitter authentication OK")
        twit_ok = True
    except:
        print("Error during Twitter authentication")
        return None

    # Check if token is expired
    dbResponse = table.get_item(Key={'spotify': 'prod'})
    expiresAt = dbResponse['Item']['expiresAt']
    if expiresAt <= time.time():
        refreshTheToken(refreshToken)

    # Get Token
    dbResponse = table.get_item(Key={'spotify': 'prod'})
    accessToken = dbResponse['Item']['accessToken']

    # Make Spotify Request
    isPlaying, currBio, newBio = makeRequest(accessToken)
    
    # Make Twitter Request
    if isPlaying:
        newBio = newBio[:160]
        print(newBio)
        twit_api.update_profile(description=newBio)
    elif getCurrBioAddOnIndex() != -1:
        print("nothing playing, but rewriting bio")
        twit_api.update_profile(description=currBio)
    else:
        pass

