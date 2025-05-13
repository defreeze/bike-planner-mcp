
def get_weather_forecast(location: str) -> dict:
    # Simulated static weather
    return {
        "location": location,
        "forecast": [
            {"day": "Tomorrow", "condition": "sunny", "high": 22, "low": 14},
            {"day": "Day After", "condition": "cloudy", "high": 19, "low": 13}
        ]
    }
