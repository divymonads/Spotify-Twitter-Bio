import spotipy, tweepy
import spotipy.util as util
from login_data import SPOTIPY_USERNAME, SPOTIPY_SCOPE, SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET
from login_data import TW_ACCESS_TOKEN, TW_ACCESS_SECRET, TW_API_KEY, TW_API_SECRET
import pprint
import sys


# Spotify API
token = util.prompt_for_user_token(SPOTIPY_USERNAME,
SPOTIPY_SCOPE,
client_id=SPOTIPY_CLIENT_ID,
client_secret=SPOTIPY_CLIENT_SECRET,
redirect_uri='https://twitter.com/divywonder')
if token:
    print('Spotify Credentials OK')
else:
    print("Error during Spotify authentication")
    twit_ok = False
    sys.exit()


# Authenticate to Twitter
auth = tweepy.OAuthHandler(TW_API_KEY, TW_API_SECRET)
auth.set_access_token(TW_ACCESS_TOKEN, TW_ACCESS_SECRET)

twit_api = tweepy.API(auth)

# Check Functionality
try: 
    twit_api.verify_credentials()
    print("Twitter authentication OK")
    twit_ok = True
except:
    print("Error during Twitter authentication")
    twit_ok = False
    sys.exit()


bio_add_on = (" | 🎶 listening to ") 

def getCurrBio():
    curr_bio = twit_api.me()._json['description']
    x = curr_bio.rfind(bio_add_on)
    if x != -1:
        curr_bio = curr_bio[:x]
    return curr_bio

def getNewBio():
    bio_str = bio_add_on + currently_playing['item']['artists'][0]['name']
    curr_bio = getCurrBio()
    new_bio = curr_bio + bio_str 
    return curr_bio, new_bio

def main_procedure():
    sp = spotipy.Spotify(auth=token)
    currently_playing = sp.currently_playing()
    pp = pprint.PrettyPrinter(indent=4)

    if currently_playing and currently_playing['is_playing']: 
        curr_bio, new_bio = getNewBio()
    else:
        new_bio = getCurrBio()
   
    # Just basic maxlength requirement
    new_bio = new_bio[:160]

    twit_api.update_profile(description=new_bio)
    
    print(new_bio)

def lambda_handler(_event_json, _context):
    if token and twit_ok:
        main_procedure()
