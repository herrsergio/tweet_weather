import tweepy
from configparser import ConfigParser
from urllib import error, parse, request
import json
import sys
import datetime

BASE_WEATHER_API_URL = "http://api.openweathermap.org/data/2.5/weather"
PADDING = 20
THUNDERSTORM = range(200, 300)
DRIZZLE = range(300, 400)
RAIN = range(500, 600)
SNOW = range(600, 700)
ATMOSPHERE = range(700, 800)
CLEAR = range(800, 801)
CLOUDY = range(801, 900)


def _get_OW_api_key():
    """Fetch the API key from your configuration file.

    Expects a configuration file named "secrets.ini" with structure:

        [openweather]
        api_key=<YOUR-OPENWEATHER-API-KEY>
    """
    config = ConfigParser()
    config.read("secrets.ini")
    return config["openweather"]["api_key"]


def _get_TW_apis_key(description):
    """Fetch the API key from your configuration file.

    Expects a configuration file named "secrets.ini" with structure:

        [openweather]
        api_key=<YOUR-OPENWEATHER-API-KEY>
    """
    config = ConfigParser()
    config.read("secrets.ini")
    return config["twitter"][description]


def build_weather_query(city_input, imperial=False):
    """Builds the URL for an API request to OpenWeather's weather API.

    Args:
        city_input (List[str]): Name of a city as collected by argparse
        imperial (bool): Whether or not to use imperial units for temperature

    Returns:
        str: URL formatted for a call to OpenWeather's city name endpoint
    """
    api_key = _get_OW_api_key()
    url_encoded_city_name = parse.quote(city_input)
    units = "imperial" if imperial else "metric"
    url = (
        f"{BASE_WEATHER_API_URL}?q={url_encoded_city_name}"
        f"&units={units}&appid={api_key}&lang=en"
    )
    return url


def get_openmeteo_historical_temp(lat, lon, dt_date):
    """Fetches historical temperature from exactly 1 year ago using Open-Meteo Archive API."""
    date_str = dt_date.strftime("%Y-%m-%d")
    hour = dt_date.hour
    
    url = (
        f"https://archive-api.open-meteo.com/v1/archive"
        f"?latitude={lat}&longitude={lon}"
        f"&start_date={date_str}&end_date={date_str}"
        f"&hourly=temperature_2m"
    )
    
    req = request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    response = request.urlopen(req)
    data = json.loads(response.read())
    
    target_time_str = f"{date_str}T{hour:02d}:00"
    times = data["hourly"]["time"]
    temps = data["hourly"]["temperature_2m"]
    
    if target_time_str in times:
        idx = times.index(target_time_str)
        return temps[idx]
    else:
        return temps[12]


def get_weather_data(query_url):
    """Makes an API request to a URL and returns the data as a Python object.

    Args:
        query_url (str): URL formatted for OpenWeather's city name endpoint

    Returns:
        dict: Weather information for a specific city
    """
    try:
        response = request.urlopen(query_url)
    except error.HTTPError as http_error:
        if http_error.code == 401:  # 401 - Unauthorized
            sys.exit("Invalid API key")
        elif http_error.code == 404:  # 404 - Not Found
            sys.exit("Error: Can't find city name")
        else:
            sys.exit(f"Something went wrong... ({http_error.code})")
    data = response.read()

    try:
        return json.loads(data)
    except json.JSONDecodeError:
        sys.exit("Error: Couldn't decode JSON data")


def display_weather_info(weather_data, historical_temp=None, imperial=False):
    """Prints formatted weather information about a city.

    Args:
        weather_data (dict): API response from OpenWeather by city name
        historical_temp (float): Temperature from 1 year ago
        imperial (bool): Whether or not to use imperial units for temperature

    More information at https://openweathermap.org/current#name
    """
    city = weather_data["name"]
    weather_id = weather_data["weather"][0]["id"]
    weather_description = weather_data["weather"][0]["description"]
    temperature = weather_data["main"]["temp"]

    weather_symbol = _select_weather_display_params(weather_id)

    output = f"{city:^{PADDING}}"
    output = output+f"\t{weather_symbol}"
    output = output+f"\t{weather_description.capitalize():^{PADDING}}"
    
    if historical_temp is not None:
        output = output+f"({temperature}°{'F' if imperial else 'C'}) ({historical_temp}°{'F' if imperial else 'C'} last year)\n"
    else:
        output = output+f"({temperature}°{'F' if imperial else 'C'})\n"

    return output


def _select_weather_display_params(weather_id):
    if weather_id in THUNDERSTORM:
        display_params = ("💥")
    elif weather_id in DRIZZLE:
        display_params = ("💧")
    elif weather_id in RAIN:
        display_params = ("💦")
    elif weather_id in SNOW:
        display_params = ("⛄️")
    elif weather_id in ATMOSPHERE:
        display_params = ("🌀")
    elif weather_id in CLEAR:
        display_params = ("🔆")
    elif weather_id in CLOUDY:
        display_params = ("💨")
    else:  # In case the API adds new weather codes
        display_params = ("🌈")
    return display_params


def tweet_weather(event, context):

    consumer_key = _get_TW_apis_key("consumer_key")
    consumer_secret = _get_TW_apis_key("consumer_secret")

    access_token = _get_TW_apis_key("access_token")
    access_token_secret = _get_TW_apis_key("access_token_secret")

    client = tweepy.Client(
        consumer_key=consumer_key, consumer_secret=consumer_secret,
        access_token=access_token, access_token_secret=access_token_secret
    )

    dt_1y_ago_date = datetime.datetime.now() - datetime.timedelta(days=365)

    def get_weather_str(city_name):
        query_url = build_weather_query(city_name)
        weather_data = get_weather_data(query_url)
        lat = weather_data["coord"]["lat"]
        lon = weather_data["coord"]["lon"]
        try:
            hist_temp = get_openmeteo_historical_temp(lat, lon, dt_1y_ago_date)
        except Exception as e:
            print(f"Failed to fetch historical data for {city_name}: {e}")
            hist_temp = None
        return display_weather_info(weather_data, hist_temp)

    weather_cdmx = get_weather_str("Mexico City")
    weather_snfcso = get_weather_str("San Francisco")
    weather_sntpburg = get_weather_str("Saint Petersburg")

    message = str(weather_cdmx).strip()+"\n\n"+str(weather_snfcso).strip()+"\n\n"+str(weather_sntpburg).strip()
    print(message)

    response = client.create_tweet(text=message)

    return 1
