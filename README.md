<div align="center">

# 🌬️ WindScope

### UK Wind Forecast Intelligence for Day-Ahead Power Buyers

**See exactly which wind forecast was available when the buying decision had to be made, and measure how wrong it was.**

![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-5-646CFF?logo=vite&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![Backend tests](https://img.shields.io/badge/pytest-23%20passed-brightgreen)
![Frontend tests](https://img.shields.io/badge/vitest-3%20passed-brightgreen)

### 🔗 [Live App](PASTE_DEPLOYED_URL) &nbsp;|&nbsp; 🎥 [Video Demo](PASTE_UNLISTED_YOUTUBE_URL)

<!-- Replace the two links above. Keep the text, only change the URL inside ( ). -->

<br/>

<!-- HERO SCREENSHOT: full dashboard, dark theme, default cutoff selected -->
<img src="docs/screenshots/dashboard-hero.png" alt="WindScope dashboard" width="95%"/>

</div>

---

## 📌 Table of Contents

1. [The Problem](#-the-problem)
2. [What WindScope Does](#-what-windscope-does)
3. [Screenshots and Live Demo](#-screenshots-and-live-demo)
4. [Key Findings for January 2026](#-key-findings-for-january-2026)
5. [How the Analysis Works](#-how-the-analysis-works)
6. [Architecture](#-architecture)
7. [Tech Stack](#-tech-stack)
8. [Repository Structure](#-repository-structure)
9. [Getting Started](#-getting-started)
10. [API Reference](#-api-reference)
11. [Testing](#-testing)
12. [Deployment](#-deployment)
13. [Assumptions and Limitations](#-assumptions-and-limitations)
14. [AI Tool Disclosure](#-ai-tool-disclosure)

---

## 🎯 The Problem

A UK energy utility has to buy electricity on the **day-ahead wholesale market**. Orders are locked one day before delivery, so the buyer must decide **before** they know how much wind will actually blow.

Wind output is weather dependent. Whatever the forecast fails to cover must be bought from other sources such as thermal plants. That raises two questions:

1. **Which wind forecast was actually available at the moment of the decision?**
2. **How accurate were such forecasts, in numbers, so the error can be priced into the purchase?**

WindScope answers both using national level data from Elexon BMRS only: **FUELHH** for actual generation and **WINDFOR** for forecasts.

---

## ✨ What WindScope Does

- **No look-ahead bias.** For every delivery half hour, the app picks the latest forecast published on or before the decision cutoff. Forecasts published later are excluded.
- **Realistic decision time.** The default cutoff is the **GB day-ahead gate closure at 09:20 UK time** (EPEX GB), calculated in the `Europe/London` timezone. Other cutoffs are available for sensitivity checks.
- **Accuracy in numbers.** MAE, RMSE, bias, error percentiles (P50, P90, P95), normalised MAE, and the worst single over and under forecast.
- **Risk sizing.** A suggested shortfall buffer based on the P95 under-forecast, shown as decision support rather than advice.
- **Error by lead time.** How accuracy changes as the forecast gets older (0 to 6 hours up to 48 hours and beyond), using every forecast version and not only the selected one.
- **Forecast vintage inspector.** Click any delivery interval to see every forecast published for it, when it was published, and whether it was eligible at the cutoff.
- **Data quality panel.** Expected vs retrieved vs matched intervals, missing data, and the exact formulas used.
- **Flexible alignment.** Compare on the hour only (744 intervals) or map hourly forecasts onto both half hours (1,488 intervals).
- **Searchable, sortable table** of every interval with status (`MATCHED`, `MISSING_FORECAST`, `MISSING_ACTUAL`) and pagination.

---

## 🖼️ Screenshots and Live Demo

> GitHub cannot run JavaScript inside a README, so hover interactions cannot work here. The animated demo below shows the live behaviour instead, and the **Live App** link at the top lets reviewers try the real thing.

### Interactive chart in action

<!-- GIF: record yourself hovering and scrolling over the main chart for 5 to 10 seconds.
     Save as docs/screenshots/chart-hover.gif (keep it under 10 MB). -->
<p align="center">
  <img src="docs/screenshots/chart-hover.gif" alt="Hovering over the generation chart shows live values" width="95%"/>
</p>

### Actual vs forecast vs error

<!-- Your attached chart screenshot goes here. Save it as docs/screenshots/generation-chart.png -->
<p align="center">
  <img src="docs/screenshots/generation-chart.png" alt="Actual wind outturn compared with the selected forecast and the signed error" width="95%"/>
</p>

*Teal line: actual outturn (FUELHH). Purple line: selected forecast (WINDFOR). Orange bars: error (forecast minus actual). Above zero means the forecast was too high.*

### KPI and risk sizing cards

<!-- Save as docs/screenshots/kpi-cards.png -->
<p align="center">
  <img src="docs/screenshots/kpi-cards.png" alt="KPI cards for MAE, RMSE, bias and percentile errors" width="95%"/>
</p>

### Error by forecast lead time

<!-- Save as docs/screenshots/horizon-chart.png -->
<p align="center">
  <img src="docs/screenshots/horizon-chart.png" alt="Forecast error grouped by lead time" width="95%"/>
</p>

### Forecast vintage inspector

<!-- Save as docs/screenshots/vintage-modal.png -->
<p align="center">
  <img src="docs/screenshots/vintage-modal.png" alt="All forecast versions published for one delivery interval" width="80%"/>
</p>

### Data quality and methodology

<!-- Save as docs/screenshots/data-quality.png -->
<p align="center">
  <img src="docs/screenshots/data-quality.png" alt="Data quality and methodology panel" width="80%"/>
</p>

### Cutoff selector and table

<!-- Save as docs/screenshots/cutoff-and-table.png -->
<p align="center">
  <img src="docs/screenshots/cutoff-and-table.png" alt="Cutoff selector and interval table" width="95%"/>
</p>

---

## 📊 Key Findings for January 2026

Results for the default cutoff (day-ahead gate closure, 09:20 UK time). Error is defined as **forecast minus actual**.

**Hourly delivery periods (744 intervals)**
- MAE: **2,127 MW**, which is **18.4%** of the average actual output of 11,581 MW
- RMSE: **2,606 MW**
- Bias: **+1,852 MW** (forecast too high)
- P50 / P90 / P95 absolute error: **1,759 / 4,306 / 5,351 MW**
- Over-forecast in **631** intervals, under-forecast in **113**
- Suggested shortfall buffer (P95 of under-forecast size): **2,374 MW**
- Worst over-forecast: **+6,894 MW** on 12 Jan 01:00 UTC
- Worst under-forecast: **-3,389 MW** on 8 Jan 19:00 UTC

**Half-hourly mapping (1,488 intervals)**
- MAE **2,145 MW**, RMSE **2,616 MW**, bias **+1,852 MW**

**What this means for a buyer**

January 2026 forecasts were persistently **too optimistic about wind** by roughly 1.85 GW on average. A buyer who trusted them at face value would have under-bought backup power in most hours. Positive bias means wind was over-estimated and the missing energy had to be covered elsewhere.

**Error grows with forecast age**

- 0 to 6 h ahead: MAE **1,768 MW**
- 6 to 12 h ahead: **1,834 MW**
- 12 to 24 h ahead: **1,991 MW**
- 24 to 36 h ahead: **2,123 MW**
- 36 to 48 h ahead: **2,337 MW**
- 48 h and beyond: **2,372 MW**

*Numbers come from the cached January 2026 data and will change only if the data is refreshed.*

---

## 🧠 How the Analysis Works

### 1. Forecast selection rule

For each delivery time `T`:

1. Collect every forecast whose `startTime` is `T`.
2. Keep only those with `publishTime <= cutoff(T)`.
3. Select the one with the latest `publishTime`.
4. If none qualify, mark the interval `MISSING_FORECAST`. It is never filled with zero.

### 2. Decision cutoffs

- **`d1_0920` (default):** 09:20 UK time on the day before delivery. This matches the EPEX GB day-ahead gate closure.
- **`d1_0900`:** 09:00 UK time on D-1.
- **`d1_1200`:** 12:00 UK time on D-1. A late sensitivity case, because it includes forecasts published after the real gate closure.
- **`d1_1700`:** 17:00 UK time on D-1.
- **`lead_12h`, `lead_24h`, `lead_48h`:** a fixed lead time before each delivery interval.
- **`latest`:** the newest forecast published before delivery starts.

D-1 cutoffs are computed in `Europe/London` and converted to UTC, so the logic stays correct in summer time as well.

### 3. Metrics

```
error = forecast - actual            (MW)
MAE   = mean(|error|)
RMSE  = sqrt(mean(error^2))
Bias  = mean(error)
nMAE  = MAE / mean(actual) * 100     (%)
P50, P90, P95 = percentiles of |error|
Shortfall buffer = P95 of the size of under-forecast errors
```

- Positive error means over-forecast (wind was lower than predicted).
- Negative error means under-forecast (wind was higher than predicted).

### 4. Data cleaning

- Only `fuelType == "WIND"` is kept from FUELHH.
- Records with null, NaN or infinite values are rejected.
- Duplicate actuals on the same `startTime` keep the latest record. Duplicate forecasts on the same `(startTime, publishTime)` are removed.
- Missing values are flagged, not replaced with zero.
- All timestamps are timezone aware and normalised to UTC.

### 5. Resolution difference

FUELHH is half-hourly and WINDFOR is hourly. The app offers two alignments:

- **Exact:** evaluate only the hours where both datasets have a value (744 intervals).
- **Hourly block:** apply each hourly forecast to both half hours in that hour (1,488 intervals).

---

## 🏗️ Architecture

```
          Elexon BMRS API (FUELHH, WINDFOR)
                        |
                        v
  +-------------------------------------------------------+
  |                  FastAPI backend                      |
  |                                                       |
  |  ElexonClient --> DataCache --> DataCleaner           |
  |                                     |                 |
  |                                     v                 |
  |        Routes <-- Metrics <-- ForecastSelection       |
  +--------------------------+----------------------------+
                             | JSON over HTTP (/api)
                             v
  +-------------------------------------------------------+
  |                   React dashboard                     |
  |  Cutoff selector, KPI cards, generation chart,        |
  |  horizon chart, daily error chart, table,             |
  |  vintage modal, data quality panel                    |
  +-------------------------------------------------------+
```

**Design choices**

- **File cache instead of a database.** January 2026 is a fixed, small dataset (1,488 half hours). A cached JSON snapshot makes responses instant, avoids migrations, and keeps results reproducible even if the upstream API is slow. The cache can be rebuilt with `POST /api/analysis/refresh`.
- **Selection logic isolated in one module.** The most important business rule (no look-ahead) lives in `forecast_selection.py` with its own tests, so it is easy to review.
- **Pydantic schemas** define every response, which gives validation and automatic API docs.
- **Same-origin in Docker.** Nginx serves the frontend and proxies `/api` to the backend, so no CORS setup is needed there.

More detail is in [`docs/architecture.md`](docs/architecture.md) and [`docs/methodology.md`](docs/methodology.md).

---

## 🧰 Tech Stack

- **Frontend:** React 18, Vite 5, Tailwind CSS 3, Recharts, Lucide icons
- **Backend:** Python 3.12, FastAPI, Pydantic v2, HTTPX, Uvicorn
- **Data:** Elexon BMRS `FUELHH` and `WINDFOR` datasets, January 2026
- **Testing:** Pytest, Vitest, React Testing Library
- **Containers:** Docker, Docker Compose, multi-stage build with Nginx

---

## 📁 Repository Structure

```text
.
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI entrypoint
│   │   ├── config.py                  # Settings from environment variables
│   │   ├── api/
│   │   │   ├── routes_health.py       # GET /api/health
│   │   │   ├── routes_analysis.py     # analysis, horizon, refresh
│   │   │   ├── routes_forecasts.py    # cutoffs and vintages
│   │   │   └── routes_quality.py      # data quality report
│   │   ├── models/schemas.py          # Pydantic models
│   │   └── services/
│   │       ├── elexon.py              # Elexon API client with retries
│   │       ├── data_cache.py          # JSON cache with metadata
│   │       ├── data_cleaning.py       # Filtering, validation, deduplication
│   │       ├── forecast_selection.py  # Cutoff logic, no look-ahead rule
│   │       ├── metrics.py             # MAE, RMSE, bias, percentiles
│   │       └── data_pipeline.py       # Orchestrates the full analysis
│   ├── data/cache/                    # Cached January 2026 Elexon data
│   ├── tests/                         # Pytest suite
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.jsx                    # State and layout
│   │   ├── services/api.js            # API client
│   │   └── components/
│   │       ├── AppHeader.jsx
│   │       ├── CutoffSelector.jsx
│   │       ├── DateRangeFilter.jsx
│   │       ├── KpiCard.jsx
│   │       ├── GenerationChart.jsx
│   │       ├── HorizonChart.jsx
│   │       ├── ErrorDistributionChart.jsx
│   │       ├── ForecastTable.jsx
│   │       ├── VintageModal.jsx
│   │       ├── DataQualityPanel.jsx
│   │       ├── LoadingState.jsx
│   │       └── ErrorState.jsx
│   ├── nginx.conf                     # Serves the app, proxies /api
│   └── Dockerfile
├── docs/
│   ├── architecture.md
│   ├── methodology.md
│   ├── video_demo_script.md
│   └── screenshots/                   # Images used in this README
├── docker-compose.yml
├── pytest.ini
├── .env.example
└── README.md
```

---

## 🚀 Getting Started

### Option 1: Docker (recommended)

```bash
docker-compose up --build
```

- Dashboard: http://localhost:3000
- API: http://localhost:8000
- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/api/health

Stop with `docker-compose down`.

### Option 2: Run locally

**Backend**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend** (in a second terminal)

```bash
cd frontend
npm install
npm run dev
```

Open the URL printed by Vite (usually http://localhost:3000 or http://localhost:5173).

### Environment variables

Copy `.env.example` to `.env` if you want to change defaults.

```ini
# Backend
PORT=8000
HOST=0.0.0.0
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
ELEXON_API_BASE_URL=https://data.elexon.co.uk/bmrs/api/v1
DATA_CACHE_DIR=./data/cache

# Frontend
# Backend URL for separate deployments.
# Leave empty (VITE_API_BASE_URL=) to use same-origin /api paths.
# If not set at all, the app falls back to http://localhost:8000.
VITE_API_BASE_URL=http://localhost:8000
```

---

## 🔌 API Reference

- `GET /api/health`: service status
- `GET /api/analysis`: matched records, metrics and data quality for a chosen cutoff
  - query: `cutoff_type`, `alignment` (`exact` or `hourly_block`), `start_date`, `end_date`
- `GET /api/analysis/horizon`: error metrics grouped by forecast lead time
- `POST /api/analysis/refresh`: re-download the data from Elexon and rebuild the cache
- `GET /api/forecasts/cutoffs`: list of available decision cutoffs
- `GET /api/forecasts/vintages`: every forecast published for one delivery time
  - query: `delivery_time`, `cutoff_type`
- `GET /api/data-quality`: completeness and quality report

Interactive documentation is served at `/docs` when the backend is running.

---

## ✅ Testing

```bash
# Backend, from the project root
pytest -v

# Frontend
cd frontend
npm test

# Production build check
npm run build
```

The suite covers metric formulas with hand-calculated inputs, cutoff calculation (including the 09:19 vs 09:21 boundary), look-ahead prevention, data cleaning, horizon buckets, and the API routes.

---

## ☁️ Deployment

Live app: **PASTE_DEPLOYED_URL**

<!-- Describe exactly what you used. Keep this short and true, for example:
     Frontend on Vercel (root directory: frontend, framework: Vite, env VITE_API_BASE_URL set to the backend URL).
     Backend on Heroku or Vercel, with CORS_ORIGINS set to the frontend domain. -->

- **Frontend:** root directory `frontend`, framework preset Vite, build command `npm run build`, output directory `dist`, environment variable `VITE_API_BASE_URL` pointing at the backend.
- **Backend:** deploy the `backend` folder, set `CORS_ORIGINS` to the frontend domain and `ELEXON_API_BASE_URL` as shown above. Platforms that assign their own port (such as Heroku) should start Uvicorn on `$PORT`.

---

## ⚠️ Assumptions and Limitations

- **Scope.** National level wind data from Elexon only, for decisions made in January 2026, as the brief requires.
- **Cutoff time.** The default 09:20 UK time reflects the EPEX GB day-ahead gate closure. The N2EX auction closes a little later, at about 09:50 UK time. The 09:20 default is the earlier, more conservative choice, and the 12:00 option is kept only to show how a late cutoff changes the results.
- **Cached data.** The app ships with a cached snapshot of the January 2026 streams for speed and reproducibility. Use the refresh endpoint to pull fresh data.
- **Resolution.** Forecasts are hourly and actuals are half-hourly, so results are shown under two alignment modes.
- **Single month.** Findings such as the +1.85 GW bias describe January 2026 and should not be generalised to other months without more data.

---

## 🤖 AI Tool Disclosure

Google DeepMind **Antigravity** was used to assist with architecture planning, component scaffolding, test drafting, and documentation. All code, formulas, data pipelines and tests were reviewed, run and verified by me.

---

<div align="center">

Built for the REint Full Stack SWE challenge.

</div>
