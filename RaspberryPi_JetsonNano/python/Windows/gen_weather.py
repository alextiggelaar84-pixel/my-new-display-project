import requests
import json
import os
# 1. Define your API key and the base URL
# Replace 'YOUR_API_KEY' with the actual key from your weather API provider
API_KEY = "73b61aea7126a9c6f78d3bc4c75d6a79"
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

# 2. Set up the target location and parameters
city_name = "New York"
params = {
    "q": city_name,
    "appid": API_KEY,
    "units": "metric"  # Use 'imperial' for Fahrenheit, 'metric' for Celsius
}

try:
    # 3. Send the HTTP GET request
    response = requests.get(BASE_URL, params=params, timeout=10)
    
    # Check if the request was successful (Status Code 200)
    response.raise_for_status()
    
    # 4. Convert response to a Python dictionary
    weather_data = response.json()
    
    # 5. Extract and print specific details from the JSON payload
    temperature = weather_data["main"]["temp"]
    humidity = weather_data["main"]["humidity"]
    description = weather_data["weather"][0]["description"]
    print(os.path.abspath("data.json"))
    with open("data.json", "w+") as f:
        json.dump(weather_data, f, indent=4)
    print(f"--- Weather in {city_name} ---")
    print(f"Temperature: {temperature}°C")
    print(f"Humidity: {humidity}%")
    print(f"Condition: {description.capitalize()}")

except requests.exceptions.HTTPError as http_err:
    print(f"HTTP error occurred: {http_err} (Check your API key or city name)")
except Exception as err:
    print(f"An error occurred: {err}")
