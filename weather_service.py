import os
import requests
from dotenv import load_dotenv


load_dotenv()                # reads .env into environment
WEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')
if not WEATHER_API_KEY:
    raise RuntimeError("Missing OPENWEATHER_API_KEY")

BASE_URL = 'https://api.openweathermap.org/data/2.5/weather'


def get_current_weather(city: str = 'Moscow', units: str = 'metric') -> dict:
    """
    Fetches current weather data for the given city from OpenWeatherMap.

    Args:
        city (str): Name of the city (default: 'Moscow').
        units (str): Units of measurement. 'metric' returns Celsius (default).

    Returns:
        dict: A dictionary containing key weather details:
            - description: Weather condition description
            - temperature: Current temperature
            - feels_like: Perceived temperature
            - humidity: Humidity percentage
            - wind_speed: Wind speed
    """

    params = {
        'q': city,
        'appid': WEATHER_API_KEY,
        'units': units
    }
    resp = requests.get(BASE_URL, params=params)
    resp.raise_for_status()
    data = resp.json()

    # Extract relevant fields
    weather = {
        'description': data['weather'][0]['description'],
        'temperature': data['main']['temp'],
        'feels_like': data['main']['feels_like'],
        'humidity': data['main']['humidity'],
        'wind_speed': data['wind']['speed']
    }
    return weather
