# The Spotify Twitter Bio

This project integrates spotify's currently playing and recently played into twitter bios.

## How it works

This is a Lambda solution. I've uploaded a different copy of the code into a Lambda in my free-tier AWS account.

It uses the spotify's web api and the Tweepy API. 

If you need an introduction to Twitter bots and the Tweepy API on Lambda.

It saves a copy of your user spotify API token into DynamoDB with an expiration date. It checks if it's expired, and updates accordingly. I took the basic idea of this from Josh Spicer's website, since my original version wasn't automating the authentication.

Gets the currently playing from the website and tacks it onto your twitter bio. It's a bit fickle but works. Just a small weekend project! If nothing's playing then it'll display recently played.

![Screenshot of Twitter Bio](./screenshot.png?raw=true "Screenshot")

## Requirements

- boto3==1.14.38
- botocore==1.17.38
- certifi==2020.6.20
- chardet==3.0.4
- docutils==0.15.2
- idna==2.10
- jmespath==0.10.0
- oauthlib==3.1.0
- PySocks==1.7.1
- python-dateutil==2.8.1
- requests==2.24.0
- requests-oauthlib==1.3.0
- s3transfer==0.3.3
- six==1.15.0
- tweepy==3.9.0
- urllib3==1.25.10
