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
            measurements = client.get_measurements_last_n_days(1)
            with_soc = [m for m in measurements if m.get("state_of_charge_percent") is not None]
            if not with_soc:
                self._respond(404, {"error": "No state of charge data available for the last 24 hours"})
                return
            min_m = min(with_soc, key=lambda m: m["state_of_charge_percent"])
            self._respond(200, {
                "min_state_of_charge_percent": min_m["state_of_charge_percent"],
                "period_start": min_m["period_start"],
                "period_end": min_m["period_end"],
            })
        except GridleAPIError as e:
            self._respond(e.status_code, {"error": str(e)})

    def _respond(self, status, body):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())
