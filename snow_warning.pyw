from datetime import datetime
import json
import requests


class Weather:
    def __init__(self, weather_data: dict) -> None:
        self.time = datetime.fromtimestamp(weather_data["dt"])
        self.temp: float = weather_data["main"]["temp"]

        weather = weather_data["weather"][0]
        self.short: str = weather["main"].lower().strip()
        self.long: str = weather["description"].lower().strip()

    def __str__(self) -> str:
        return f"{self.time}: {self.temp}° {self.short} ({self.long})"
    
    def has(self, weather: str) -> bool:
        return weather in self.short or weather in self.long


def get_config() -> (dict[str, any], str):
    """Return the params for the weather request and the url for the webhook"""
    with open("config.json") as config_file:
        return json.load(config_file)
    
def find_ice(weather_data: list[Weather]):
    max_freeze_delay = 3
    max_freeze_temp = -1
    last_rain = None
    time_since_rain = 0

    for weather in weather_data:
        if weather.has("rain"):
            time_since_rain = 0
            last_rain = weather.long

        if time_since_rain < max_freeze_delay \
        and weather.temp <= max_freeze_temp:
            return (weather.time, last_rain, time_since_rain * 3)
        
        else:
            time_since_rain += 1

    return None

def find_snow(weather_data: list[Weather]) -> Weather | None:
    for weather in weather_data:
        if weather.has("snow"):
            return weather        

def main() -> None:
    (request_parameters, webhook_url) = get_config()
    
    response = requests.get(
        "https://api.openweathermap.org/data/2.5/forecast",
        request_parameters
    )

    weather_data = [Weather(point) for point in response.json()["list"]]

    payload = {}

    first_snow = find_snow(weather_data)
    first_ice = find_ice(weather_data)

    if first_snow:
        msg = f"{first_snow.long} possible at {first_snow.time}"
        payload["snow"] = msg
        print(msg)

    if first_ice:
        (time, rain, h_since) = first_ice
        msg = f"ice possible at {time} ({rain} {h_since} hours ago)"
        payload["ice"] = msg
        print(msg)

    if payload:
        requests.post(
            webhook_url,
            json=payload
        )


if __name__ == "__main__":
    main()
