# WindScope — Methodology & Mathematical Formulations

## 1. Domain Context & Procurement Problem

In Great Britain's wholesale electricity market, utilities must purchase power to satisfy forecasted consumer demand. Day-ahead market trading occurs on Day $D-1$ for electricity delivery during Day $D$. 

Because wind energy generation is weather-dependent and non-dispatchable, trading teams need accurate forecasts of available wind power to determine how much residual thermal, hydro, or imported power must be procured on the wholesale market.

Overforecasting wind power causes under-procurement on the day-ahead market, forcing the utility into the balancing mechanism or cash-out penalties. Conversely, underforecasting wind power causes over-procurement of expensive thermal power.

---

## 2. Decision Cutoff & Anti-Lookahead Selection Rule

### 2.1 The Need for an Explicit Cutoff

For any given delivery timestamp $T$, meteorological forecast providers issue multiple revisions (vintages) over time. However, electricity procurement decisions are locked at specific market deadlines before delivery. Evaluating a forecast published *after* the auction deadline introduces **look-ahead bias**, misrepresenting the information actually available to traders at decision time.

### 2.2 Formal Selection Rule

Let:
- $T$ = Target delivery timestamp (e.g., `2026-01-15T12:00:00Z`).
- $D$ = Calendar delivery date of $T$.
- $C(T)$ = Decision cutoff timestamp for delivery interval $T$.
- $\mathcal{F}(T) = \{ F_1, F_2, \dots, F_k \}$ = Set of all published forecast records for target delivery interval $T$, where each record $F_i$ has publication timestamp $P(F_i)$ and forecast generation $G(F_i)$.

The **Eligible Forecast Set** $\mathcal{E}(T)$ is defined as:
$$\mathcal{E}(T) = \{ F \in \mathcal{F}(T) \mid P(F) \le C(T) \}$$

The **Selected Forecast** $F^*(T)$ is the latest eligible publication:
$$F^*(T) = \operatorname*{argmax}_{F \in \mathcal{E}(T)} P(F)$$

If $\mathcal{E}(T) = \emptyset$, no eligible forecast was available by the cutoff, and the interval is flagged as `MISSING_FORECAST`.

### 2.3 Supported Cutoff Strategies

All Day-Ahead cutoffs are evaluated in the `Europe/London` timezone (via Python `zoneinfo`) and converted to UTC, ensuring resilience to British Summer Time (BST) outside winter months:

1. **Day-Ahead 09:20 UK time (`d1_0920`) — Default Benchmark**:
   $$C(T) = (D - 1 \text{ day}) \text{ at 09:20:00 UK local time (converted to UTC)}$$
   *Rationale*: Corresponds directly to the EPEX SPOT GB Day-Ahead wholesale auction gate closure (10:20 CET / 09:20 UK). Using later cutoffs introduces look-ahead bias by incorporating forecasts that were not available when traders committed order books.
2. **Day-Ahead 09:00 UK time (`d1_0900`)**:
   $$C(T) = (D - 1 \text{ day}) \text{ at 09:00:00 UK local time}$$
   *Rationale*: Pre-auction desk briefing snapshot prior to gate closure.
3. **Day-Ahead 12:00 UK time (`d1_1200`) — Late / Sensitivity Case**:
   $$C(T) = (D - 1 \text{ day}) \text{ at 12:00:00 UK local time}$$
   *Rationale*: Sensitivity case after real gate closure, previously used in preliminary analysis.
4. **Day-Ahead 17:00 UK time (`d1_1700`)**:
   $$C(T) = (D - 1 \text{ day}) \text{ at 17:00:00 UK local time}$$
   *Rationale*: Post-auction evening physical notification schedule.
5. **Rolling Lead-Time Cutoffs (`lead_24h`, `lead_12h`, `lead_48h`)**:
   $$C(T) = T - \Delta t \quad \text{where } \Delta t \in \{12\text{h}, 24\text{h}, 48\text{h}\}$$
6. **Intraday / Gate Closure (`latest`)**:
   $$C(T) = T$$
   Latest forecast published on or before the start of delivery interval $T$.

---

## 3. Forecast Error Metrics

All error calculations are computed strictly over the valid matched intervals where both actual outturn $A_i$ and selected forecast $F_i$ exist.

### 3.1 Sign Convention

$$\text{Error}_i = F_i - A_i$$

- **$\text{Error}_i > 0$ (Overforecast)**: The forecast predicted higher wind generation than materialized. The trader under-procures conventional power.
- **$\text{Error}_i < 0$ (Underforecast)**: The forecast predicted lower wind generation than materialized. The trader over-procures conventional power.

### 3.2 Mean Absolute Error (MAE)

$$\text{MAE} = \frac{1}{n} \sum_{i=1}^n \left| F_i - A_i \right|$$

- **Unit**: Megawatts (MW).
- **Interpretation**: The expected average error magnitude regardless of direction.

### 3.3 Root Mean Squared Error (RMSE)

$$\text{RMSE} = \sqrt{\frac{1}{n} \sum_{i=1}^n \left( F_i - A_i \right)^2}$$

- **Unit**: Megawatts (MW).
- **Interpretation**: Heavily penalizes large error outliers, reflecting the non-linear risk of wholesale imbalance cash-out prices.

### 3.4 Forecast Bias (Mean Signed Error)

$$\text{Bias} = \frac{1}{n} \sum_{i=1}^n \left( F_i - A_i \right)$$

- **Unit**: Megawatts (MW).
- **Interpretation**: Identifies systematic overestimation ($\text{Bias} > 0$) or underestimation ($\text{Bias} < 0$) in the numerical weather models.

### 3.5 Normalised MAE (nMAE %)

$$\text{nMAE} = \frac{\text{MAE}}{\frac{1}{n}\sum_{i=1}^n A_i} \times 100\%$$

- **Interpretation**: Scales absolute forecast deviation against mean actual generation, enabling cross-month and cross-portfolio benchmarking.

### 3.6 Risk-Sizing Percentiles & Procurement Buffers

- **P50 / P90 / P95 Absolute Error**: Computed via linear interpolation over sorted absolute errors $|F_i - A_i|$.
- **Suggested Wind Shortfall Buffer (P95 Under-Forecast)**: 95th percentile of $(A_i - F_i)$ when actuals exceed forecasts ($A > F$). In procurement, this represents the volume of thermal/flexible capacity a trader should reserve to mitigate unexpected wind drops.
- **P95 Over-Forecast Boundary**: 95th percentile of $(F_i - A_i)$ when forecasts exceed actuals ($F > A$).

### 3.7 Lead-Time Horizon Error Analysis

For each forecast record across all published vintages, lead time is defined as:
$$\text{Lead} = \text{deliveryTime} - \text{publishTime} \quad (\text{hours})$$
Evaluated across six standard operational horizons: `0–6h`, `6–12h`, `12–24h`, `24–36h`, `36–48h`, and `48h+`.

---

## 4. Elexon BMRS Dataset Reconciliation

### 4.1 Resolution Difference

- **`FUELHH` (Actual Generation)**:
  - Half-hourly resolution (30-minute intervals).
  - January 2026 total intervals: $31 \times 48 = 1,488$ intervals.
  - All 1,488 records are present in the official Elexon dataset (100% complete).
- **`WINDFOR` (Forecast Generation)**:
  - Hourly snapshots (`:00` timestamps).
  - January 2026 unique delivery hours: $31 \times 24 = 744$ hours.
  - Total publication records across all vintages: ~18,080.

### 4.2 Alignment Modes

WindScope provides transparent support for both evaluation perspectives:
1. **Exact Alignment (`exact`)**:
   Evaluates only the 744 hourly timestamps (`:00`) where both datasets natively share identical delivery timestamps.
2. **Hourly Block Mapping (`hourly_block`)**:
   Maps each hourly forecast $F(H)$ to both half-hour intervals of that hour ($H:00$ and $H:30$), evaluating all 1,488 intervals of the month.

---

## 5. Verified January 2026 Performance Metrics

Computed on official Elexon January 2026 datasets with the default **Day-Ahead 09:20 UK time (EPEX GB)** cutoff:

| Metric | Exact Hourly (`exact`, $n=744$) | Hourly Block (`hourly_block`, $n=1488$) |
| :--- | :--- | :--- |
| **Mean Absolute Error (MAE)** | **2,127.48 MW** | **2,145.17 MW** |
| **Root Mean Squared Error (RMSE)** | **2,606.07 MW** | **2,615.81 MW** |
| **Forecast Bias** | **+1,851.53 MW** (Over-forecast) | **+1,851.90 MW** (Over-forecast) |
| **Normalised MAE (nMAE)** | **18.37%** (Mean: 11,581.11 MW) | **18.52%** (Mean: 11,580.74 MW) |
| **P50 Absolute Error (Median)** | **1,758.50 MW** | **1,795.50 MW** |
| **P90 Absolute Error** | **4,306.40 MW** | **4,274.90 MW** |
| **P95 Absolute Error** | **5,350.90 MW** | **5,340.95 MW** |
| **Suggested Shortfall Buffer (P95 Under-Forecast)** | **2,374.00 MW** | **2,333.40 MW** |
| **P95 Over-Forecast Boundary** | **5,504.50 MW** | **5,431.70 MW** |
| **Worst Over-Forecast** | **+6,894.00 MW** (2026-01-12 01:00Z) | **+6,894.00 MW** (2026-01-12 01:00Z) |
| **Worst Under-Forecast** | **-3,389.00 MW** (2026-01-08 19:00Z) | **-3,835.00 MW** (2026-01-08 18:30Z) |
| **Interval Completeness** | **100% (744/744)** | **100% (1,488/1,488)** |
