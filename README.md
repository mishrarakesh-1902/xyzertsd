# WindScope — UK Wind Forecast Intelligence
### Full-Stack Renewable Energy Forecast Analysis Platform | React + Python + Docker

[![Backend Tests](https://img.shields.io/badge/pytest-23%20passed-emerald)](backend/tests)
[![Frontend Tests](https://img.shields.io/badge/vitest-3%20passed-emerald)](frontend/src/App.test.jsx)
[![Docker](https://img.shields.io/badge/docker--compose-ready-blue)](docker-compose.yml)
[![FastAPI](https://img.shields.io/badge/backend-FastAPI%200.110-teal)](backend/app)
[![React](https://img.shields.io/badge/frontend-React%2018%20%2B%20Vite-indigo)](frontend)

---

## Live Demo & Video Presentation

- **Live app**: <PASTE_DEPLOYED_URL>
- **Video demo**: <PASTE_UNLISTED_YOUTUBE_URL>

---

## 1. Project Name & Overview

**WindScope** is a specialized energy analytics and intelligence platform built for electricity trading desks participating in the United Kingdom Day-Ahead wholesale power market. 

The application evaluates national-level renewable wind generation forecasts against actual metered outturns published by **Elexon BMRS** for **January 2026**, quantifying forecast error and error bias to inform Day-Ahead wholesale procurement decisions.

---

## 2. Business Problem & Objective

An energy utility operating in the UK wholesale electricity market must purchase electricity one day prior to delivery to reliably meet consumer demand.

1. **Weather Dependency**: Wind power generation is intermittent and weather-dependent. Trading teams need to know how much electricity must be additionally procured (e.g. from thermal or hydro plants) beyond expected wind power.
2. **Day-Ahead Gate Closures**: The GB Day-Ahead auction gate closures occur on Day $D-1$ at approximately **09:20 UK time** for EPEX GB (10:20 CET) and **09:50 UK time** for N2EX. Procurement commitments are locked in at that point. Using a later cutoff (such as 12:00 or 17:00) allows the analysis to consume forecasts a trader would not have had at gate closure. WindScope defaults strictly to **Day-Ahead 09:20 UK time (EPEX GB)** computed in the `Europe/London` timezone.
3. **Core Objectives**:
   - **Historical Forecast Visibility**: Clearly understand the exact renewable generation forecasts that were available when purchasing decisions had to be made (strictly eliminating look-ahead bias).
   - **Quantitative Accuracy & Risk-Sizing**: Measure Mean Absolute Error (MAE), Root Mean Squared Error (RMSE), Forecast Bias, Normalised MAE (nMAE %), Error percentiles (P50, P90, P95), and empirical shortfall buffers to inform procurement decisions.
   - **Lead-Time Horizon Analysis**: Evaluate how forecast accuracy decays as lead time increases from 0-6 hours up to 48+ hours ahead.

---

## 3. Main Features

- **Anti-Lookahead Decision Snapshot**: Selects the latest eligible forecast published *on or before* the market decision cutoff (default: **Day-Ahead 09:20 UK time EPEX GB**, with sensitivity options for 09:00, 12:00 late case, 17:00, rolling 12h/24h/48h, and gate closure).
- **Lead-Time Horizon Error Curve**: Multi-horizon breakdown analyzing error growth across lead time buckets (0-6h, 6-12h, 12-24h, 24-36h, 36-48h, 48h+) across all forecast vintages.
- **Risk-Sizing & Procurement Buffer Cards**: Direct decision support featuring P50, P90, P95 absolute error, Normalised MAE %, and suggested wind shortfall buffers (P95 under-forecast boundary).
- **Interactive Time-Series Visualization**: Dual-axis chart rendering actual wind generation (FUELHH), selected forecast (WINDFOR), and signed error with hover tooltips and settlement period indicators.
- **Forecast Vintage Evolution Inspector**: Drill down into any delivery interval to view the complete publication timeline of all issued forecast updates and their cutoff eligibility status.
- **Daily Error & Bias Distribution**: Visualizes day-by-day systematic over/underforecasting tendencies.
- **Auditable Data Quality & Transparency Panel**: Transparent accounting of expected intervals (1,488 half-hours), retrieved records, missing intervals, and mathematical formulations.
- **Flexible Resolution Alignment**: Toggle between exact hourly matching (744 intervals) and half-hourly block mapping (1,488 intervals).
- **Searchable, Sortable Data Table**: Filterable by status (`MATCHED`, `MISSING_FORECAST`, `MISSING_ACTUAL`), delivery time, error magnitude, and pagination.

---

## 4. Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | React 18, Vite 5, Tailwind CSS 3, Recharts 2, Lucide Icons |
| **Backend** | Python 3.12, FastAPI, Pydantic v2, Pydantic-Settings, Uvicorn, HTTPX, python-dateutil |
| **Data Ingestion** | Official Elexon BMRS API v1 streaming endpoints (`FUELHH` and `WINDFOR`) |
| **Caching** | Local disk JSON caching with metadata tracking and automated cache warming |
| **Testing** | Pytest (Python backend unit & API tests), Vitest + React Testing Library (Frontend) |
| **Containerization** | Docker, Docker Compose, Multi-stage Node/Nginx production image |

---

## 5. Architecture Overview

```text
                                  +------------------------------+
                                  |     Elexon BMRS REST API     |
                                  |  (/datasets/FUELHH & WINDFOR)|
                                  +---------------+--------------+
                                                  | HTTP Streams
                                                  v
+-----------------------------------------------------------------------------------------+
|                                    Python FastAPI Backend                               |
|                                                                                         |
|  +---------------------+      +---------------------+      +-------------------------+  |
|  |    ElexonClient     | ---> |  DataCacheService   | ---> |       DataCleaner       |  |
|  |  (HTTPX + Retries)  |      |   (JSON Storage)    |      | (Validation & Cleaners) |  |
|  +---------------------+      +---------------------+      +------------+------------+  |
|                                                                         |               |
|                                                                         v               |
|  +---------------------+      +---------------------+      +-------------------------+  |
|  |    FastAPI Routes   | <--- |    MetricsEngine    | <--- | ForecastSelectionEngine |  |
|  | (/analysis, /vint.) |      |  (MAE, RMSE, Bias)  |      |  (Cutoff & Anti-Bias)   |  |
|  +----------+----------+      +---------------------+      +-------------------------+  |
+-------------|---------------------------------------------------------------------------+
              | JSON Over HTTP (Port 8000)
              v
+-----------------------------------------------------------------------------------------+
|                                  React 18 Dashboard UI                                  |
|                                                                                         |
|  +-------------------+  +--------------------+  +------------------+  +--------------+  |
|  |    AppHeader      |  |  Cutoff & Filters  |  |  KPI Metric Cards|  | Generation   |  |
|  |   (Sync & Pills)  |  |  (D-1 12:00, Dates)|  | (MAE, RMSE, Bias)|  | Chart & Dist|  |
|  +-------------------+  +--------------------+  +------------------+  +--------------+  |
|  +-------------------+  +--------------------+  +------------------+                    |
|  |   ForecastTable   |  |    VintageModal    |  | DataQualityPanel |                    |
|  | (Sort, Paginate)  |  | (Publication Time) |  |  (Transparency)  |                    |
|  +-------------------+  +--------------------+  +------------------+                    |
+-----------------------------------------------------------------------------------------+
```

---

## 6. Directory & File Structure

```text
windscope/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                     # FastAPI application entrypoint & lifespan
│   │   ├── config.py                   # Pydantic settings & environment configuration
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── schemas.py              # Pydantic schemas (Records, Metrics, Quality)
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── elexon.py               # Elexon BMRS client with streaming & retries
│   │   │   ├── data_cache.py           # File-based cache service with metadata
│   │   │   ├── data_cleaning.py        # Cleaning, validation, deduplication, interval grid
│   │   │   ├── forecast_selection.py   # Cutoff selection logic & anti-lookahead rule
│   │   │   ├── metrics.py              # Error formulas (MAE, RMSE, Bias)
│   │   │   └── data_pipeline.py        # End-to-end pipeline coordinator
│   │   └── api/
│   │       ├── __init__.py
│   │       ├── routes_health.py        # /api/health endpoint
│   │       ├── routes_analysis.py      # /api/analysis & /api/analysis/refresh
│   │       ├── routes_forecasts.py     # /api/forecasts/cutoffs & /api/forecasts/vintages
│   │       └── routes_quality.py       # /api/data-quality endpoint
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_health.py              # Health check tests
│   │   ├── test_data_cleaning.py       # Data cleaning, wind filtering & range checks
│   │   ├── test_forecast_selection.py  # Forecast cutoff & look-ahead prevention tests
│   │   ├── test_metrics.py             # Numerical metric unit tests with known inputs
│   │   └── test_api.py                 # Full FastAPI route integration tests
│   ├── data/
│   │   └── cache/                      # Verified pre-cached Elexon JSON datasets
│   ├── requirements.txt
│   └── Dockerfile                      # Backend container configuration
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── AppHeader.jsx           # Brand header, dataset badges, sync trigger
│   │   │   ├── KpiCard.jsx             # Key performance indicator cards with tooltips
│   │   │   ├── CutoffSelector.jsx      # Cutoff selection dropdown & resolution toggles
│   │   │   ├── DateRangeFilter.jsx     # January date presets & custom date pickers
│   │   │   ├── GenerationChart.jsx     # Recharts actuals vs forecast vs error chart
│   │   │   ├── ErrorDistributionChart.jsx # Daily bias & MAE bar chart
│   │   │   ├── HorizonChart.jsx        # Lead-time horizon error curve (0-6h to 48h+)
│   │   │   ├── ForecastTable.jsx       # Interval records table with pagination & search
│   │   │   ├── VintageModal.jsx        # Historical publication evolution modal
│   │   │   ├── DataQualityPanel.jsx    # Audit & methodology transparency modal
│   │   │   ├── LoadingState.jsx        # Animated loading spinner
│   │   │   └── ErrorState.jsx          # Error display with retry button
│   │   ├── services/
│   │   │   └── api.js                  # Centralized HTTP client for backend API
│   │   ├── App.jsx                     # Top-level state and layout container
│   │   ├── App.test.jsx                # Frontend Vitest test suite
│   │   ├── main.jsx                    # React DOM mount point
│   │   ├── index.css                   # Tailwind CSS styling & custom scrollbars
│   │   └── setupTests.js               # Jest-DOM & ResizeObserver mocks
│   ├── index.html
│   ├── vite.config.js                  # Vite & Vitest configuration
│   ├── tailwind.config.js              # Energy analytics dark theme palette
│   ├── postcss.config.js
│   ├── nginx.conf                      # Production Nginx reverse-proxy configuration
│   ├── package.json
│   └── Dockerfile                      # Multi-stage frontend container build
│
├── docs/
│   ├── architecture.md                 # Detailed architecture & design decisions
│   ├── methodology.md                  # Mathematical formulations & selection rules
│   └── video_demo_script.md            # 10-minute video demo recording script
│
├── docker-compose.yml                  # Root orchestration for full stack
├── pytest.ini                          # Pytest configuration
├── .gitignore
├── .env.example
└── README.md
```

---

## 7. Official Elexon Data Sources

The platform consumes strictly the two mandatory Elexon BMRS datasets:

1. **Actual Outturn: `FUELHH` (Half-Hourly Generation by Fuel Type)**
   - Official Documentation: `https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream`
   - Verified API Endpoint: `https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH/stream`
   - Query Parameters: `settlementDateFrom=2026-01-01&settlementDateTo=2026-01-31`
2. **Forecast Generation: `WINDFOR` (Wind Generation Forecast)**
   - Official Documentation: `https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR/stream`
   - Verified API Endpoint: `https://data.elexon.co.uk/bmrs/api/v1/datasets/WINDFOR/stream`
   - Query Parameters: `publishDateTimeFrom=2025-12-30T00:00:00Z&publishDateTimeTo=2026-02-01T00:00:00Z`

---

## 8. Field Definitions & Units

### FUELHH (Actual Generation)
- `startTime`: Target settlement interval delivery time in UTC (resolution of 30 minutes).
- `settlementDate`: Calendar date of settlement period (`YYYY-MM-DD`).
- `settlementPeriod`: UK half-hour settlement period index (1 to 48).
- `fuelType`: Generation fuel type. Filtered strictly to `"WIND"`.
- `generation`: Verified metered actual wind generation outturn in Megawatts (**MW**).
- `publishTime`: Timestamp when actual outturn was published.

### WINDFOR (Forecast Generation)
- `startTime`: Delivery interval being forecast in UTC (hourly `:00` snapshots).
- `publishTime`: Exact timestamp when the forecast was generated/published by meteorological models.
- `generation`: Forecasted national wind generation in Megawatts (**MW**).

---

## 9. January 2026 Analysis Scope

- **Delivery Window**: `2026-01-01T00:00:00Z` through `2026-01-31T23:30:00Z` (31 days).
- **Expected Half-Hour Delivery Intervals**: $31 \times 48 = 1,488$ intervals.
- **Handling of Boundaries**:
  - Forecasts published in late December 2025 (e.g. Dec 30-31) that forecast January 2026 delivery intervals are **preserved**.
  - Any delivery intervals falling in February 2026 are **strictly excluded**.
  - Forecasts published after the decision cutoff for a given delivery interval are excluded from that snapshot to prevent look-ahead bias.

---

## 10. Forecast Selection Rule

For each delivery interval $T$:
1. Identify all forecast records with delivery target $T$.
2. Filter the records to those published on or before the decision cutoff $C(T)$:
   $$\text{publishTime} \le C(T)$$
3. Select the eligible record with the greatest publication timestamp:
   $$\text{selected forecast} = \operatorname*{argmax}_{F \in \text{eligible}} \text{publishTime}(F)$$
4. If no eligible forecast exists (all were published after the cutoff), mark the interval as `MISSING_FORECAST`.

---

## 11. Decision Cutoff Assumptions

Wholesale power auction schedules govern when trading commitments lock. In the UK market, the GB Day-Ahead auction gate closure occurs on Day $D-1$ at **09:20 UK time** for EPEX SPOT GB (10:20 CET) and **09:50 UK time** for Nord Pool N2EX. 

To strictly prevent look-ahead bias, cutoffs are evaluated in the `Europe/London` timezone (via Python's `zoneinfo` with IANA tzdata) and converted to UTC:

1. **Day-Ahead 09:20 UK (`d1_0920`) — Default Benchmark**:
   - Cutoff: $(D - 1 \text{ day})$ at 09:20:00 UK local time (`Europe/London`).
   - *Rationale*: Matches the actual EPEX SPOT GB Day-Ahead auction gate closure. Using 12:00 allows an analysis to access forecasts published after bids close, misrepresenting information traders actually possessed.
2. **Day-Ahead 09:00 UK (`d1_0900`)**:
   - Cutoff: $(D - 1 \text{ day})$ at 09:00:00 UK local time (`Europe/London`).
   - *Rationale*: Pre-auction morning briefing snapshot 20 minutes prior to order book closure.
3. **Day-Ahead 12:00 UK (`d1_1200`) — Late / Sensitivity Case**:
   - Cutoff: $(D - 1 \text{ day})$ at 12:00:00 UK local time (`Europe/London`).
   - *Rationale*: Sensitivity case after real gate closure, previously used as an informal benchmark.
4. **Day-Ahead 17:00 UK (`d1_1700`)**:
   - Cutoff: $(D - 1 \text{ day})$ at 17:00:00 UK local time (`Europe/London`).
   - *Rationale*: Post-auction evening physical notification schedule.
5. **Rolling Lead-Time Cutoffs (`lead_24h`, `lead_12h`, `lead_48h`)**:
   - Cutoff: Delivery timestamp minus 24, 12, or 48 hours.
6. **Gate Closure / 0h Lead Time (`latest`)**:
   - Cutoff: Target delivery timestamp ($T$).

---

## 12. Timestamp & Timezone Conventions

- All timestamps are parsed into **timezone-aware UTC datetime objects** and normalized to ISO-8601 strings (`YYYY-MM-DDTHH:MM:SSZ`).
- The UK is on Greenwich Mean Time (GMT, UTC+0) during January.
- Delivery records are matched strictly by delivery timestamp (`startTime`), never by publication timestamp.

---

## 13. Data Cleaning & Missing-Data Handling

- **Wind Filtering**: Actual records from FUELHH are filtered strictly for `fuelType == 'WIND'`. Non-wind records (CCGT, Nuclear, Solar, Biomass, etc.) are discarded.
- **Finite Values**: Any record with null, NaN, or infinite generation values is rejected.
- **Missing vs. Zero**: Missing records are never converted into artificial zero generation. Missing values are flagged with explicit statuses (`MISSING_ACTUAL`, `MISSING_FORECAST`).
- **Deduplication**: Duplicate actual records on the same `startTime` are resolved by retaining the latest outturn; duplicate forecast records on `(startTime, publishTime)` are removed.

---

## 14. Forecast Error Metrics & Formulas

All metrics are computed strictly over valid matched intervals ($n$):

### Sign Convention
$$\text{Error}_i = \text{Forecast}_i - \text{Actual}_i$$
- **Positive Error ($>0$)**: Overforecast (forecast exceeded actual outturn).
- **Negative Error ($<0$)**: Underforecast (forecast fell short of actual outturn).

### Mean Absolute Error (MAE)
$$\text{MAE} = \frac{1}{n} \sum_{i=1}^n \left| \text{Forecast}_i - \text{Actual}_i \right|$$

### Root Mean Squared Error (RMSE)
$$\text{RMSE} = \sqrt{\frac{1}{n} \sum_{i=1}^n \left( \text{Forecast}_i - \text{Actual}_i \right)^2}$$

### Forecast Bias (Mean Signed Error)
$$\text{Bias} = \frac{1}{n} \sum_{i=1}^n \left( \text{Forecast}_i - \text{Actual}_i \right)$$

### Normalised MAE (nMAE %)
$$\text{nMAE} = \frac{\text{MAE}}{\frac{1}{n}\sum_{i=1}^n \text{Actual}_i} \times 100\%$$

### Risk-Sizing Percentiles & Decision Buffers
- **P50 / P90 / P95 Absolute Error**: Computed via linear interpolation over sorted $|e_i|$.
- **Suggested Wind Shortfall Buffer (P95 Under-Forecast)**: 95th percentile of $(Actual - Forecast)$ on intervals where actual wind exceeded forecast ($A > F$). In procurement, this represents the generation buffer to cover downside wind risk.
- **Over-Forecast Boundary (P95 Over-Forecast)**: 95th percentile of $(Forecast - Actual)$ on intervals where wind was over-estimated ($F > A$).

---

## 15. January 2026 Computed Baseline Performance

Under the domain-accurate **Day-Ahead 09:20 UK time (EPEX GB)** default cutoff:

| Metric | Exact Hourly (`exact`) | Half-Hourly Block (`hourly_block`) |
| :--- | :--- | :--- |
| **Evaluated Intervals ($n$)** | **744 / 744 (100%)** | **1,488 / 1,488 (100%)** |
| **Mean Absolute Error (MAE)** | **2,127.48 MW** | **2,145.17 MW** |
| **Root Mean Squared Error (RMSE)** | **2,606.07 MW** | **2,615.81 MW** |
| **Forecast Bias** | **+1,851.53 MW** (Over-forecast) | **+1,851.90 MW** (Over-forecast) |
| **Normalised MAE (nMAE)** | **18.37%** (Mean: 11,581.11 MW) | **18.52%** (Mean: 11,580.74 MW) |
| **P50 Absolute Error (Median)** | **1,758.50 MW** | **1,795.50 MW** |
| **P90 Absolute Error** | **4,306.40 MW** | **4,274.90 MW** |
| **P95 Absolute Error** | **5,350.90 MW** | **5,340.95 MW** |
| **Suggested Wind Shortfall Buffer** | **2,374.00 MW** | **2,333.40 MW** |
| **P95 Over-Forecast Boundary** | **5,504.50 MW** | **5,431.70 MW** |
| **Worst Single Over-Forecast** | **+6,894.00 MW** (2026-01-12 01:00Z) | **+6,894.00 MW** (2026-01-12 01:00Z) |
| **Worst Single Under-Forecast** | **-3,389.00 MW** (2026-01-08 19:00Z) | **-3,835.00 MW** (2026-01-08 18:30Z) |

### Forecast Error by Lead-Time Horizon (All Vintages)

| Horizon Bucket | MAE (MW) | RMSE (MW) | Bias (MW) | Sample Size ($n$) |
| :--- | :--- | :--- | :--- | :--- |
| **0–6h Ahead** | 1,767.72 MW | 2,249.21 MW | +1,548.25 MW | 1,488 |
| **6–12h Ahead** | 1,833.73 MW | 2,304.38 MW | +1,616.10 MW | 1,488 |
| **12–24h Ahead** | 1,990.88 MW | 2,474.17 MW | +1,811.20 MW | 2,976 |
| **24–36h Ahead** | 2,122.56 MW | 2,586.87 MW | +1,838.48 MW | 2,976 |
| **36–48h Ahead** | 2,337.01 MW | 2,866.21 MW | +2,004.50 MW | 2,945 |
| **48h+ Ahead** | 2,371.92 MW | 2,977.90 MW | +1,479.56 MW | 2,510 |

*Key Takeaway*: Forecast error increases with lead time: the 0-6h Ahead horizon achieved the lowest MAE (1,767.72 MW), while the 48h+ Ahead horizon had the highest uncertainty (2,371.92 MW MAE).

---

## 16. Installation & Prerequisites

- **Python**: 3.11 or 3.12 (with `tzdata` for Windows timezone resolution)
- **Node.js**: v18+ or v20+
- **Docker**: Version 24+ with Docker Compose v2+ (Optional for containerized run)

---

## 17. How to Start the Backend Locally

```bash
# 1. Navigate to backend directory
cd backend

# 2. Create virtual environment and activate
python -m venv .venv

# Windows PowerShell:
.\.venv\Scripts\Activate.ps1

# Linux / macOS:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
The backend API and interactive OpenAPI documentation will be live at:
- **API URL**: `http://localhost:8000`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`

---

## 18. How to Start the Frontend Locally

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Start development server
npm run dev
```
The React frontend dashboard will be live at:
- **Dashboard URL**: `http://localhost:3000` (or `http://localhost:5173`)

---

## 19. How to Run Automated Tests

### Backend Unit & Integration Tests (Pytest)
```bash
# From the project root:
.\backend\.venv\Scripts\pytest.exe -v

# Or from inside backend/:
pytest -v
```
*Result: 23 automated tests passing (Metrics, Risk-Sizing, Horizon, Forecast Selection, Data Cleaning, Health, and API Endpoints).*

### Frontend Component Tests (Vitest)
```bash
# From inside frontend/:
npm test
```
*Result: 3 test suites passing (App rendering, KPI metrics, Horizon chart, and error handling).*

### Frontend Production Build Verification
```bash
# From inside frontend/:
npm run build
```

---

## 20. How to Run with Docker Compose

To build and run the entire production-grade multi-container stack with a single command:

```bash
docker-compose up --build
```
- **Frontend Dashboard**: `http://localhost:3000`
- **Backend API**: `http://localhost:8000`
- **Health Check**: `http://localhost:8000/api/health`

To stop:
```bash
docker-compose down
```

---

## 21. Required Environment Variables

Copy `.env.example` to `.env`:

```ini
# Backend Configuration
PORT=8000
HOST=0.0.0.0
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173
ELEXON_API_BASE_URL=https://data.elexon.co.uk/bmrs/api/v1
DATA_CACHE_DIR=./data/cache

# Frontend Configuration
# Uses nullish coalescing (??):
# - Set to an empty string ("") for same-origin relative /api paths (e.g. reverse proxy)
# - Set to an absolute URL (e.g. https://api.yourdomain.com) for cross-origin deployments
# - Leave unset/undefined to fall back to http://localhost:8000 for local development
VITE_API_BASE_URL=http://localhost:8000
```

---

## 22. Deployment Instructions

### Frontend Deployment on Vercel
1. Set the root directory to `frontend`.
2. Framework Preset: `Vite`.
3. Build Command: `npm run build`.
4. Output Directory: `dist`.
5. Environment Variable: Set `VITE_API_BASE_URL` to your deployed backend URL (e.g. `https://your-backend.herokuapp.com`).

### Backend Deployment on Heroku
1. Create a Heroku application using the Python buildpack (or container stack).
2. Set root context or deploy `backend/` subtree.
3. Configure environment variables in the Heroku Dashboard:
   - `PORT=8000`
   - `CORS_ORIGINS=https://<YOUR_VERCEL_FRONTEND_DOMAIN>`
   - `ELEXON_API_BASE_URL=https://data.elexon.co.uk/bmrs/api/v1`

---

## 23. Links to Deployed Application & Repository

- **Live app**: <PASTE_DEPLOYED_URL>
- **Video demo**: <PASTE_UNLISTED_YOUTUBE_URL>
- **Public GitHub Repository**: Anonymous submission repository

---

## 24. Known Limitations & Upstream Characteristics

1. **Time Resolution Asymmetry**:
   - `FUELHH` outturn is published half-hourly (1,488 intervals for January 2026).
   - `WINDFOR` forecasts are published on the hour (744 unique intervals).
   - *Resolution*: WindScope handles this transparently via its `exact` and `hourly_block` alignment selectors.
2. **Historical Data vs. Live Streaming**:
   - The platform includes verified local caching for January 2026 Elexon streams to guarantee sub-second performance and resilience against upstream Elexon downtime. The cache can be refreshed on demand via `POST /api/analysis/refresh`.

---

## 25. AI Tool Disclosure

In compliance with the assignment submission requirements:
- **AI Coding Assistant**: Google DeepMind Antigravity was used to assist with architectural planning, component scaffolding, test drafting, and documentation synthesis. All code, data pipelines, mathematical formulas, and tests have been independently implemented, verified, and executed.

---

## 26. Design Decisions & Trade-Offs

- **FastAPI over Django/Flask**: Selected for native asynchronous support, Pydantic v2 type safety, high throughput, and automatic OpenAPI schema generation.
- **In-Memory + File Caching over Relational Database**: Avoided unnecessary PostgreSQL/SQLite overhead since the January 2026 dataset is bounded (1,488 delivery periods). JSON caching provides instantaneous response times, zero database migrations, and 100% reproducibility.
- **Modular Frontend**: Separation of UI into dedicated components (`AppHeader`, `CutoffSelector`, `KpiCard`, `GenerationChart`, `ForecastTable`, `VintageModal`, `DataQualityPanel`) enables clean maintainability and isolated testing.
