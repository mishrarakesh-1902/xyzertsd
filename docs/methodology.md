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

1. **Day-Ahead 12:00 UTC (`d1_1200`) — Default Benchmark**:
   $$C(T) = (D - 1 \text{ day}) \text{ at 12:00:00 UTC}$$
   *Rationale*: Matches the standard daily auction gate closure on the UK EPEX SPOT and Nord Pool wholesale power exchanges.
2. **Day-Ahead 17:00 UTC (`d1_1700`)**:
   $$C(T) = (D - 1 \text{ day}) \text{ at 17:00:00 UTC}$$
   *Rationale*: Post-auction evening schedule finalization.
3. **Day-Ahead 09:00 UTC (`d1_0900`)**:
   $$C(T) = (D - 1 \text{ day}) \text{ at 09:00:00 UTC}$$
   *Rationale*: Pre-auction morning trading preparation.
4. **Rolling Lead-Time Cutoffs (`lead_24h`, `lead_12h`, `lead_48h`)**:
   $$C(T) = T - \Delta t$$
   where $\Delta t \in \{12\text{h}, 24\text{h}, 48\text{h}\}$.
5. **Intraday / Gate Closure (`latest`)**:
   $$C(T) = T$$
   Latest forecast published on or before the start of the delivery interval.

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
