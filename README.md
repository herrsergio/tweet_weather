# Tweet Weather

An active Twitter bot implemented as a Serverless AWS Lambda function that posts automated weather updates natively using the Tweepy library. 

Every two hours, the bot evaluates conditions for predefined cities (Mexico City, San Francisco, and Saint Petersburg)—extracting the current conditions, current temperature, and exactly the temperature at the same hour from 1 year ago—and tweets a formatted summary.

Behind the scenes:
- **Current Data:** It relies on the OpenWeather `2.5/weather` API to fetch real-time geographic data and the current reading.
- **Historical Data:** It transparently queries the free Open-Meteo `archive-api` to pull exactly 1-year ago temperature history without additional cost or API keys. 

## Setup & Configuration

Before deploying, you must provide your API keys to authorize Twitter posts and OpenWeather fetches.

1. Create a `secrets.ini` file in the root directory (you can copy `secrets.ini.skel` as a starting point).
2. Fill in your respective keys:

```ini
[twitter]
consumer_key=YOUR_CONSUMER_KEY
consumer_secret=YOUR_CONSUMER_SECRET
access_token=YOUR_ACCESS_TOKEN
access_token_secret=YOUR_ACCESS_TOKEN_SECRET

[openweather]
api_key=YOUR_OPENWEATHER_API_KEY
```

## Deployment

The project relies on the Serverless Framework to easily deploy the Python code as an AWS Lambda function running in the `us-east-1` region (configurable inside `serverless.yml`).

### Prerequisites
Make sure you have Node.js, `npm`, and `serverless` globally installed.

```bash
# Set your AWS programmatic credentials
export AWS_ACCESS_KEY_ID=XXX
export AWS_SECRET_ACCESS_KEY=XXX

cd tweet_weather

# Setup a clean Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Optional: Generate requirements.txt if dependencies changed
# pip install pipreqs
# python3 -m pipreqs.pipreqs . --force

# Install the serverless plugin that packages the Python zip
serverless plugin install -n serverless-python-requirements

# Deploy to AWS Lambda!
sls deploy
```

Once the `sls deploy` command succeeds, AWS EventBridge will automatically invoke the `tweet_weather` function every 2 hours as configured in the `serverless.yml`.
