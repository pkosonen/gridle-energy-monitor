"""
Gridle Residential API client.

API docs: https://residential.gridle.com/api/public/docs
Rate limits: 1 req/s (burst 2), 1500 req/day (resets 00:00 UTC)
"""

import time
from datetime import datetime, timezone, timedelta
from typing import Optional

import requests


BASE_URL = "https://residential.gridle.com/api/public"
MAX_RANGE_DAYS = 31


class GridleAPIError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(f"HTTP {status_code}: {message}")


class GridleClient:
    def __init__(self, api_key: str, rate_limit_delay: float = 1.1):
        """
        Args:
            api_key: Your x-api-key value.
            rate_limit_delay: Seconds to wait between requests (default 1.1 to
                              stay safely within the 1 req/s limit).
        """
        self.session = requests.Session()
        self.session.headers.update({"x-api-key": api_key})
        self.rate_limit_delay = rate_limit_delay
        self._last_request_time: float = 0.0

    def _get(self, path: str, params: dict) -> list[dict]:
        # Enforce rate limit
        elapsed = time.monotonic() - self._last_request_time
        wait = self.rate_limit_delay - elapsed
        if wait > 0:
            time.sleep(wait)

        url = f"{BASE_URL}{path}"
        resp = self.session.get(url, params=params)
        self._last_request_time = time.monotonic()

        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 401:
            raise GridleAPIError(401, "Invalid or missing API key")
        elif resp.status_code == 403:
            raise GridleAPIError(403, "API key is not authorized")
        elif resp.status_code == 422:
            raise GridleAPIError(422, f"Invalid parameters: {resp.text}")
        elif resp.status_code == 429:
            raise GridleAPIError(429, "Rate limit exceeded")
        else:
            raise GridleAPIError(resp.status_code, resp.text)

    def get_measurements(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> list[dict]:
        """
        Fetch energy measurements.

        Args:
            start_time: Start of the query range (timezone-aware recommended).
            end_time:   End of the query range (timezone-aware recommended).
                        The range may not exceed 31 days.

        Returns:
            List of measurement dicts (5-minute intervals), each containing:
              - period_start, period_end (ISO 8601 strings)
              - battery_power_kw, solar_power_kw, grid_power_kw, house_power_kw (nullable)
              - solar_array_1_power_kw, solar_array_2_power_kw (nullable)
              - solar_to_house_kw, solar_to_battery_kw, solar_to_grid_kw (nullable)
              - grid_to_house_kw, grid_to_battery_kw (nullable)
              - battery_to_house_kw, battery_to_grid_kw (nullable)
              - state_of_charge_percent (nullable)
              - spot_price_cents_per_kwh (nullable)
              - battery_temperature_celsius (nullable)
        """
        if start_time and end_time:
            delta = end_time - start_time
            if delta.total_seconds() < 0:
                raise ValueError("start_time must be before end_time")
            if delta.days > MAX_RANGE_DAYS:
                raise ValueError(
                    f"Time range exceeds {MAX_RANGE_DAYS} days "
                    f"({delta.days} days requested)"
                )

        params: dict = {}
        if start_time:
            params["start_time"] = _fmt(start_time)
        if end_time:
            params["end_time"] = _fmt(end_time)

        return self._get("/measurements", params)

    def get_measurements_last_n_days(self, days: int = 7) -> list[dict]:
        """Convenience wrapper: fetch the last N days of measurements (max 31)."""
        if days > MAX_RANGE_DAYS:
            raise ValueError(f"days must be <= {MAX_RANGE_DAYS}")
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=days)
        return self.get_measurements(start_time=start, end_time=now)

    def get_measurements_today(self) -> list[dict]:
        """Fetch measurements from midnight UTC today until now."""
        now = datetime.now(timezone.utc)
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return self.get_measurements(start_time=start, end_time=now)


def _fmt(dt: datetime) -> str:
    """Format a datetime as an ISO 8601 string with UTC offset."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


# ---------------------------------------------------------------------------
# Quick demo — run with:  python gridle_client.py
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import json
    import os

    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    os.environ.setdefault(key.strip(), value.strip())

    API_KEY = os.getenv("GRIDLE_API_KEY")
    if not API_KEY:
        raise SystemExit("Error: GRIDLE_API_KEY environment variable is not set")
    client = GridleClient(api_key=API_KEY)

    print("Fetching today's measurements …")
    data = client.get_measurements_today()
    print(f"Received {len(data)} data points.\n")

    if data:
        print("Most recent data point:")
        print(json.dumps(data[-1], indent=2))

        # Summary stats (skip nulls)
        def avg(key):
            vals = [p[key] for p in data if p.get(key) is not None]
            return sum(vals) / len(vals) if vals else None

        print("\n--- Averages for today ---")
        for field in (
            "solar_power_kw",
            "solar_array_1_power_kw",
            "solar_array_2_power_kw",
            "grid_power_kw",
            "house_power_kw",
            "battery_power_kw",
            "state_of_charge_percent",
            "spot_price_cents_per_kwh",
            "battery_temperature_celsius",
        ):
            value = avg(field)
            print(f"  {field}: {value:.3f}" if value is not None else f"  {field}: n/a")
