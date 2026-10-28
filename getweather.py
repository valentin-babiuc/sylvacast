import requests

def get_coordinates(city_name):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": city_name, "format": "json", "limit": 1}

    try:
        response = requests.get(url, params=params,
                                headers={'User-Agent': 'SylvaCast/1.0 (student project)'},
                                timeout=15)

        response.raise_for_status()

        data = response.json()

        if data:
            lat = data[0]['lat']
            lon = data[0]['lon']
            return (lat, lon)
        else:
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error connecting to the geocoding service: {e}")
        return None

def get_weather_data(lat, lon, date):
    url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date={date}&end_date={date}&hourly=temperature_2m,relative_humidity_2m,weather_code"

    try:
        response = requests.get(url, timeout=30)

        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"Error connecting to the weather service: {e}")
        return None

def interpret_weather_code(code):
    weather_codes = {
        0: "Cer senin",
        1: "Predominant senin",
        2: "Parțial noros",
        3: "Acoperit",
        45: "Ceață",
        48: "Ceață cu chiciură",
        51: "Burniță ușoară",
        53: "Burniță moderată",
        55: "Burniță densă",
        56: "Burniță înghețată ușoară",
        57: "Burniță înghețată densă",
        61: "Ploaie ușoară",
        63: "Ploaie moderată",
        65: "Ploaie abundentă",
        66: "Ploaie înghețată ușoară",
        67: "Ploaie înghețată abundentă",
        71: "Ninsoare ușoară",
        73: "Ninsoare moderată",
        75: "Ninsoare abundentă",
        77: "Granule de zăpadă",
        80: "Averse ușoare de ploaie",
        81: "Averse moderate de ploaie",
        82: "Averse violente de ploaie",
        85: "Averse ușoare de ninsoare",
        86: "Averse abundente de ninsoare",
        95: "Furtună cu descărcări electrice",
        96: "Furtună cu grindină ușoară",
        99: "Furtună cu grindină abundentă"
    }
    return weather_codes.get(code, "Unknown weather condition")

def fetch_history(lat: float, lon: float, start: str, end: str) -> list:
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude":   lat,
        "longitude":  lon,
        "start_date": start,
        "end_date":   end,
        "daily":      "temperature_2m_max,relative_humidity_2m_mean",
        "timezone":   "auto",
    }

    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    dates    = data["daily"]["time"]
    temps    = data["daily"]["temperature_2m_max"]
    humidity = data["daily"].get("relative_humidity_2m_mean", [None] * len(dates))

    return [
        {"date": d, "temp": t, "humidity": h}
        for d, t, h in zip(dates, temps, humidity)
        if t is not None
    ]