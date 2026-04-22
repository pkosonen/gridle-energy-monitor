"""
Flask server exposing Gridle data to the React frontend.
"""

import os
from flask import Flask, jsonify
from flask_cors import CORS
from gridle_client import GridleClient, GridleAPIError


def _load_dotenv():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    os.environ.setdefault(key.strip(), value.strip())


_load_dotenv()

API_KEY = os.getenv("GRIDLE_API_KEY")
if not API_KEY:
    raise RuntimeError("GRIDLE_API_KEY environment variable is not set")

app = Flask(__name__)
CORS(app)

client = GridleClient(api_key=API_KEY)


@app.route("/api/latest")
def latest():
    """Return the single most recent measurement."""
    try:
        data = client.get_measurements_today()
        if not data:
            return jsonify({"error": "No data available for today"}), 404
        return jsonify(data[-1])
    except GridleAPIError as e:
        return jsonify({"error": str(e)}), e.status_code


@app.route("/api/today")
def today():
    """Return all measurements from today."""
    try:
        data = client.get_measurements_today()
        return jsonify(data)
    except GridleAPIError as e:
        return jsonify({"error": str(e)}), e.status_code


if __name__ == "__main__":
    print("Gridle API server running at http://localhost:5050")
    app.run(port=5050, debug=True)
