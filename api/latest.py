import json
import os
import sys
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gridle_client import GridleClient, GridleAPIError


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        api_key = os.environ.get("GRIDLE_API_KEY")
        if not api_key:
            self._respond(500, {"error": "GRIDLE_API_KEY is not configured"})
            return
        try:
            client = GridleClient(api_key=api_key)
            data = client.get_measurements_today()
            if not data:
                self._respond(404, {"error": "No data available for today"})
                return
            self._respond(200, data[-1])
        except GridleAPIError as e:
            self._respond(e.status_code, {"error": str(e)})

    def _respond(self, status, body):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())
