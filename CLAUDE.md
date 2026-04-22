# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

A real-time home energy monitoring dashboard. A Python Flask backend proxies the [Gridle Residential API](https://residential.gridle.com) and exposes two endpoints; a React + Vite frontend polls every 30 seconds and renders the data as a dark-themed dashboard.

## Running the app

Start both servers in separate terminals:

```bash
# Backend (port 5050)
python server.py

# Frontend (port 5173)
cd frontend && npm run dev
```

Open `http://localhost:5173`. The frontend hardcodes `http://localhost:5050` as the API base URL (`App.jsx` line 4).

## Environment

Copy `.env.example` to `.env` and fill in the key:

```
GRIDLE_API_KEY=your_api_key_here
```

`server.py` and the `gridle_client.py` demo both load `.env` automatically via an inline loader (no `python-dotenv` required). An already-exported shell variable takes precedence (`os.environ.setdefault`).

## Frontend commands

```bash
cd frontend
npm run dev       # dev server with HMR
npm run build     # production build
npm run lint      # ESLint
npm run preview   # preview production build
```

## Git workflow

After every meaningful change, commit locally and push to GitHub so there is always a clean restore point.

```bash
git add <changed files>
git commit -m "short description of what changed and why"
git push origin main
```

Commit message guidelines:
- Start with a verb in the imperative: *Add*, *Fix*, *Remove*, *Update*, *Rename*
- One concise subject line (under 72 characters)
- If more context is needed, leave a blank line and add a short body paragraph

Examples of good messages:
- `Add battery temperature to latest API response`
- `Fix rate-limit sleep not applied on first request`
- `Remove hardcoded API key fallback from server.py`

## Architecture

```
Browser → React (Vite, :5173)
              ↓ fetch /api/latest every 30 s
         Flask (:5050)   ← server.py
              ↓ GridleClient
         Gridle Residential API
         https://residential.gridle.com/api/public
```

**`gridle_client.py`** — standalone API client.
- `GridleClient(api_key)` is the only class.
- `get_measurements(start, end)` is the core method; `get_measurements_today()` and `get_measurements_last_n_days(n)` are convenience wrappers.
- Enforces the API's rate limits: 1 req/s (burst 2), 1 500 req/day. The `_get()` method sleeps between calls.
- Raises `GridleAPIError` (carries `.status_code`) on non-2xx responses.
- Run `python gridle_client.py` directly for a quick smoke-test.

**`server.py`** — thin Flask wrapper around `GridleClient`.
- `GET /api/latest` — last measurement from today.
- `GET /api/today` — all measurements from today.
- CORS enabled (needed for the Vite dev server origin).

**`frontend/src/App.jsx`** — single-component React app.
- Fetches `/api/latest`; renders power cards, bidirectional energy-flow rows, SoC progress bar, spot price, and battery temperature.
- Color-coding: spot price green below 0 ¢/kWh, red above 10 ¢/kWh.
- Theme variables live in `index.css`; layout in `App.css`.
