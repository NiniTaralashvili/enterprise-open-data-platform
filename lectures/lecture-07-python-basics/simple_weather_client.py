import requests


def get_weather(latitude: float, longitude: float) -> dict:
    response = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,wind_speed_10m",
            "timezone": "Asia/Tbilisi",
        },
        timeout=10,
    )
    response.raise_for_status()
    return response.json()
if __name__ == "__main__":
    weather = get_weather(41.7151, 44.8271)
    print(weather["current"])