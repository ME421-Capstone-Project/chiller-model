import requests
import os
from dotenv import load_dotenv

# Load your API key from .env file
load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY")

def degrees_to_cardinal(degrees):
    """
    Convert wind direction in degrees to cardinal direction.
    """
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    index = round(degrees / 45) % 8
    return directions[index]

def get_weather(city):
    """
    Fetch weather for the given city and print it nicely.
    """
    url = "https://api.openweathermap.org/data/2.5/weather"
    
    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric"
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    city_name = data["name"]
    temp = data["main"]["temp"]
    description = data["weather"][0]["description"]
    
    # Wind data
    wind_speed = data["wind"]["speed"]
    wind_deg = data["wind"].get("deg", 0)  # Some responses may not include deg
    wind_dir = degrees_to_cardinal(wind_deg)
    
    print(f"In {city_name}, it is {temp}°C with {description}.")
    print(f"Wind: {wind_speed} m/s from the {wind_dir} ({wind_deg}°).")

# Try it
get_weather("Raleigh")
