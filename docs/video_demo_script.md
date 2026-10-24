# Video Demonstration Script & Recording Guide
## UK Wind Forecast Analysis Platform (WindScope)
**Target Total Duration**: Under 10 minutes (Strict limit)  
**Structure**: Part 1: Customer Overview (0:00 - 5:00) | Part 2: Technical Review (5:00 - 10:00)

---

## Part 1: Customer-Facing Overview (Max 5 Minutes)
**Objective**: Pitch the application to the electricity trading team, demonstrating how WindScope solves the day-ahead procurement challenge and quantifies forecast risk.

### Scene 1: Introduction & The Wholesale Trading Problem (0:00 - 1:15)
- **On Screen**: WindScope dashboard main view with January 2026 data loaded.
- **Talking Points**:
  - *"Welcome. Today we are presenting WindScope, an intelligence platform designed specifically for the UK wholesale electricity trading desk."*
  - *"As a UK energy utility, our mission is to purchase power on the day-ahead wholesale market to reliably meet consumer demand. Because wind is weather-dependent and non-dispatchable, we must accurately forecast expected wind generation to know how much conventional or thermal power to procure."*
  - *"Decisions are locked at the Day-Ahead auction—typically 12:00 GMT on Day D-1. If we overforecast wind, we under-procure power and face costly imbalance penalties in the balancing mechanism. If we underforecast, we overpay for expensive thermal capacity."*
  - *"WindScope was built to solve two critical problems: 1) Give traders complete visibility into the exact forecast available when buying decisions are made, and 2) Quantitatively evaluate forecast accuracy and error bias."*

### Scene 2: January 2026 Performance & Core KPIs (1:15 - 2:30)
- **On Screen**: Highlight the 5 KPI cards at the top.
- **Talking Points**:
  - *"Here we examine the complete delivery period of January 2026—1,488 half-hour settlement intervals."*
  - *"Under the standard Day-Ahead 12:00 UTC auction benchmark:"*
    - **Mean Absolute Error (MAE)**: ~2,002 MW on average deviation.
    - **Root Mean Squared Error (RMSE)**: ~2,470 MW, highlighting sensitivity to extreme forecast swing events.
    - **Forecast Bias**: +1,805 MW. Point out the badge: *"Notice this critical insight: the Day-Ahead forecasts in January 2026 exhibited a persistent overforecasting bias of 1.8 GW on average. Knowing this bias allows the trading desk to apply a margin of safety and avoid under-hedging."*
    - **Matched Intervals & Completeness**: 100% of actual outturn intervals verified from official Elexon FUELHH streams.

### Scene 3: Time-Series & Error Exploration (2:30 - 3:45)
- **On Screen**: Hovering over the GenerationChart and Daily Bias chart.
- **Talking Points**:
  - *"In the central visualization, the teal line represents actual wind outturn, the indigo line shows our Day-Ahead selected forecast, and the amber bars represent our signed error ($F - A$)."*
  - *"Traders can inspect any delivery interval. Notice how during high-wind ramp events (such as January 10-12), the forecast significantly overshot outturn."*
  - *"Down in the daily bias chart, we can see exactly which days were overforecasted versus underforecasted at a glance."*

### Scene 4: Interval Drilldown & Vintage Inspection (3:45 - 4:45)
- **On Screen**: Scroll to the Forecast Table. Click the **"Vintages"** button on an interval (e.g., Jan 15 12:00 UTC). Open the VintageModal.
- **Talking Points**:
  - *"Forecasts are continuously updated by meteorological providers. If we click 'Vintages' on any settlement period, WindScope displays the full publication evolution leading up to delivery."*
  - *"Notice the cutoff eligibility badge: forecasts published before our Day-Ahead 12:00 cutoff are marked 'Eligible'—and WindScope selects the latest eligible forecast. Forecasts published after the auction are marked 'Excluded' to strictly prevent look-ahead bias."*

### Scene 5: Wrap-up & Transition (4:45 - 5:00)
- **Talking Points**:
  - *"WindScope gives our trading team the quantitative evidence needed to bid intelligently, protect margins, and minimize balancing penalties. Now let's review the technical architecture."*

---

## Part 2: Internal Technical Review (Max 5 Minutes)
**Objective**: Review the software architecture, engineering standards, data pipeline, anti-lookahead algorithm, and testing suite for technical leads.

### Scene 6: Architecture & Technology Stack (5:00 - 6:00)
- **On Screen**: Show the project file structure and `docs/architecture.md`.
- **Talking Points**:
  - *"The application is architected cleanly with a decoupled React frontend and a Python FastAPI backend, containerized via Docker."*
  - *"Frontend: Built with React 18, Vite, Tailwind CSS, and Recharts. Communication is centralized through an asynchronous HTTP service client with environment-aware URL configuration."*
  - *"Backend: FastAPI on Python 3.12, utilizing Pydantic v2 schemas for strict data validation, `httpx` with exponential backoff for upstream Elexon streaming APIs, and a persistent caching layer."*

### Scene 7: Elexon Ingestion & Data Cleaning Pipeline (6:00 - 7:00)
- **On Screen**: Code view of `backend/app/services/data_cleaning.py`.
- **Talking Points**:
  - *"We ingest two official Elexon BMRS datasets: FUELHH for half-hourly outturn and WINDFOR for forecasts."*
  - *"Our data cleaner enforces several critical business rules:"*
    1. Filters strictly for `fuelType == 'WIND'` and rejects non-wind fuel types.
    2. Validates finite, non-null numerical values. Never converts missing data to artificial zeros.
    3. Normalizes all timestamps to timezone-aware UTC ISO-8601 strings.
    4. Deduplicates records on `startTime` for actuals and `(startTime, publishTime)` for forecasts.
    5. Preserves forecasts published in December 2025 that target January 2026 deliveries, while strictly excluding February deliveries.

### Scene 8: Forecast Selection Algorithm & Look-Ahead Prevention (7:00 - 8:00)
- **On Screen**: Code view of `backend/app/services/forecast_selection.py`.
- **Talking Points**:
  - *"The core algorithm prevents look-ahead bias. For each delivery timestamp $T$, the cutoff timestamp $C(T)$ is computed based on the configured policy—such as Day-Ahead 12:00 UTC (D-1 12:00)."*
  - *"Only records with $publishTime \le C(T)$ are eligible. From this eligible set, the latest publication ($\max(publishTime)$) is selected."*
  - *"We also provide resolution flexibility: exact hourly (:00) matching versus hourly-block mapping across both half-hours."*

### Scene 9: Mathematical Metrics & Verification (8:00 - 8:45)
- **On Screen**: Code view of `backend/app/services/metrics.py`.
- **Talking Points**:
  - *"All error metrics follow the standard sign convention: $error = forecast - actual$."*
  - *"MAE is $\text{mean}(|F - A|)$, RMSE is $\sqrt{\text{mean}((F - A)^2)}$, and Bias is $\text{mean}(F - A)$."*
  - *"Zero-division and empty-array guards return typed null results rather than NaNs or runtime exceptions."*

### Scene 10: Automated Tests, Docker & Deployment (8:45 - 10:00)
- **On Screen**: Terminal running `pytest` and `npm test`, showing passing tests.
- **Talking Points**:
  - *"Quality assurance is enforced with 18 automated backend tests in pytest covering metrics, data cleaning, duplicate handling, look-ahead prevention, and REST endpoints."*
  - *"The frontend is verified with Vitest and React Testing Library, testing KPI rendering, chart mounting, and error states."*
  - *"For containerization, we provide a multi-stage Dockerfile for the frontend using Nginx as a reverse proxy, and a production Python container for the backend with health checks, orchestrated via `docker-compose.yml`."*
  - *"Thank you for your review. The system is production-ready."*
