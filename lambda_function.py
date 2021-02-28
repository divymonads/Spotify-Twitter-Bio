import os, requests, time, json 
import tweepy, boto3
from enum import Enum

# Authenticate to Twitter
auth = tweepy.OAuthHandler(os.environ['TW_API_KEY'], os.environ['TW_API_SECRET'])
auth.set_access_token(os.environ['TW_ACCESS_TOKEN'], os.environ['TW_ACCESS_SECRET'])
twit_api = tweepy.API(auth)

# Connect DynamoDB database
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('SpotifyState')

# Calculate Bio Functionality
bio_marker_listening = " | 🎶 listening to " 
bio_marker_listened =" | 🎶 last listened to "
class BioStatus(Enum):
    NEUTRAL = 0
    LISTENING = 1
    LISTENED = 2

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

def getCurrentlyListeningJson(accessToken):
    headers = {'Authorization': 'Bearer ' + accessToken,
                   'Content-Type': 'application/json', 
                   'Accept': 'application/json'}
    r = requests.get('https://api.spotify.com/v1/me/player/currently-playing', headers=headers)
    try:
        r = r.json()
    except:
        print("currently played couldn't be json")
        r = None
    return r

def getLastPlayedJson(accessToken):
    print("getting last played")
    headers = {'Authorization': 'Bearer ' + accessToken,
                   'Content-Type': 'application/json', 
                   'Accept': 'application/json'}
    r = requests.get('https://api.spotify.com/v1/me/player/recently-played?limit=1', headers=headers)
    try:
        r = r.json()
    except:
        print("last played couldn't be json")
        r = None
    return r

def getBioStatus(currBio):
    x = currBio.rfind(bio_marker_listening)
    if x!=-1:
        return x, BioStatus.LISTENING
    x = currBio.rfind(bio_marker_listened)
    if x!=-1:
        return x, BioStatus.LISTENED
    return x, BioStatus.NEUTRAL

def getCurrBio():
    return twit_api.me()._json['description']

def notPlayingBio(r_json, nakedBio):
    make_twitter_request = True
    artist = r_json['items'][0]['track']['artists'][0]['name']
    newBio = nakedBio + bio_marker_listened + artist + " on spotify"
    return make_twitter_request, newBio

def playingBio(r_json, bioStatus, currBio, nakedBio):
    make_twitter_request = False
    artist = r_json['item']['artists'][0]['name']
    newBio = nakedBio + bio_marker_listening + artist + " on spotify"
    if bioStatus != BioStatus.LISTENING or currBio != newBio:
        make_twitter_request = True
    return make_twitter_request, newBio

# Get Currently Playing
# Basic Idea for refresh token renewal copied from JoshSpicer.com
def makeRequest(accessToken):
    spotify_current_json = getCurrentlyListeningJson(accessToken)

    currBio = getCurrBio()
    nakedBio = currBio    
    bioIndex, bioStatus = getBioStatus(currBio)
    if bioStatus != BioStatus.NEUTRAL:
        nakedBio = nakedBio[:bioIndex]

    toUpdate = False
    try:
        isPlaying = spotify_current_json['is_playing']
        if not isPlaying:
            if bioStatus != BioStatus.LISTENED: # change bio to listened status
                spotify_prev_json = getLastPlayedJson(accessToken)
                toUpdate, newBio = notPlayingBio(spotify_prev_json, nakedBio)
        else:
            toUpdate, newBio = playingBio(spotify_current_json, bioStatus, currBio, nakedBio)
    except:
        print("something went wrong when trying to get the new bio")
        newBio = nakedBio
        toUpdate = True
    return toUpdate, newBio



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
        print("refreshing the token")
        refreshTheToken(refreshToken)

    # Get Token
    dbResponse = table.get_item(Key={'spotify': 'prod'})
    accessToken = dbResponse['Item']['accessToken']

    # Make Request
    toUpdate, newBio = makeRequest(accessToken)
    
    # Make Twitter Request
    if toUpdate:
        newBio = newBio[:160]
        print("updating bio: \n", newBio)
        twit_api.update_profile(description=newBio)
    else:
        print("no bio to update")
