import os

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from getweather import get_coordinates, get_weather_data, interpret_weather_code
from datetime import datetime

app = Flask(__name__)

CORS(app)

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/textures/<path:filename>')
def serve_textures(filename):
    return send_from_directory('textures', filename)

@app.route('/get_weather', methods=['GET'])
def get_weather():
    city = request.args.get('city')
    date_str = request.args.get('date')

    if not city or not date_str:
        return jsonify({"error": "City and date are required."}), 400

    try:
        datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return jsonify({"error": "Invalid date format. Please use YYYY-MM-DD."}), 400

    coords = get_coordinates(city)
    if not coords:
        return jsonify({"error": f"Could not find coordinates for '{city}'."}), 404

    lat, lon = coords

    weather_data = get_weather_data(lat, lon, date_str)

    if weather_data and 'hourly' in weather_data:
        hourly = weather_data['hourly']
        temperatures = hourly.get('temperature_2m', [])
        humidity = hourly.get('relative_humidity_2m', [])
        weather_codes = hourly.get('weather_code', [])

        if temperatures and humidity and weather_codes:
            avg_temp = sum(temperatures) / len(temperatures)
            avg_humidity = sum(humidity) / len(humidity)
            from collections import Counter
            most_common_weather_code = Counter(weather_codes).most_common(1)[0][0]
            weather_description = interpret_weather_code(most_common_weather_code)

            return jsonify({
                "city": city,
                "date": date_str,
                "avg_temperature": round(avg_temp, 1),
                "avg_humidity": round(avg_humidity, 1),
                "weather_condition": weather_description
            })
        else:
            return jsonify({"error": "No weather data available for the specified date."}), 404
    else:
        return jsonify({"error": "Failed to retrieve weather data from the external service."}), 500

from getweather import fetch_history

@app.route('/api/climate-history')
def climate_history():
    lat = request.args.get('lat', 46.07, type=float)
    lon = request.args.get('lon', 23.57, type=float)
    start = request.args.get('start', '2024-01-01')
    end = request.args.get('end', '2025-01-01')
    points = request.args.get('points', 50, type=int)

    try:
        raw = fetch_history(lat, lon, start, end)

        n = len(raw)
        if n == 0:
            return jsonify({"error": "No data returned"}), 404

        if points >= n:
            sampled = raw
        else:
            indices = [int(round(i * (n - 1) / (points - 1))) for i in range(points)]
            sampled = [raw[i] for i in indices]

        return jsonify({
            "labels":      [r["date"]     for r in sampled],
            "temperature": [r["temp"]     for r in sampled],
            "humidity":    [r["humidity"] for r in sampled],
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

from ai.ai_orchestrator import handle_scenario

@app.route('/api/forestation-scenario', methods=['POST'])
def forestation_scenario():
    data = request.get_json(silent=True) or {}
    text = (data.get('text') or '').strip()
    if not text:
        return jsonify({"ok": False, "error": "Missing 'text' in request body."}), 400

    lat = data.get('lat')
    lon = data.get('lon')

    try:
        result = handle_scenario(text, lat=lat, lon=lon)
        return jsonify(result)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG') == '1')
