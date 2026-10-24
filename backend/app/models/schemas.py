from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class FuelHHRecord(BaseModel):
    startTime: str = Field(..., description="Target delivery interval time (ISO 8601 UTC)")
    publishTime: Optional[str] = Field(None, description="Actual data outturn publish timestamp")
    settlementDate: str = Field(..., description="Settlement date (YYYY-MM-DD)")
    settlementPeriod: int = Field(..., description="Settlement period (1-48)")
    fuelType: str = Field(..., description="Fuel type, e.g. WIND")
    generation: float = Field(..., description="Actual generated power in MW")

class WindforRecord(BaseModel):
    startTime: str = Field(..., description="Target delivery interval being forecast (ISO 8601 UTC)")
    publishTime: str = Field(..., description="Time forecast was generated/published (ISO 8601 UTC)")
    generation: float = Field(..., description="Forecasted wind generation in MW")

class MatchedRecord(BaseModel):
    deliveryTime: str = Field(..., description="Settlement delivery timestamp (ISO 8601 UTC)")
    settlementPeriod: Optional[int] = Field(None, description="Settlement period (1-48)")
    actualGeneration: Optional[float] = Field(None, description="Actual wind generation (MW)")
    forecastGeneration: Optional[float] = Field(None, description="Selected forecast wind generation (MW)")
    forecastPublishTime: Optional[str] = Field(None, description="Publish time of selected forecast")
    leadHours: Optional[float] = Field(None, description="Hours between forecast publication and delivery")
    error: Optional[float] = Field(None, description="error = forecast - actual (MW)")
    absError: Optional[float] = Field(None, description="|forecast - actual| (MW)")
    status: str = Field(..., description="Status: MATCHED, MISSING_FORECAST, MISSING_ACTUAL")

class ExtremeRecord(BaseModel):
    error: float = Field(..., description="Signed error (forecast - actual) in MW")
    deliveryTime: str = Field(..., description="Target delivery timestamp (ISO 8601 UTC)")
    actualGeneration: Optional[float] = Field(None, description="Actual wind generation in MW")
    forecastGeneration: Optional[float] = Field(None, description="Forecast wind generation in MW")

class AnalysisMetrics(BaseModel):
    mae: Optional[float] = Field(None, description="Mean Absolute Error in MW: mean(|forecast - actual|)")
    rmse: Optional[float] = Field(None, description="Root Mean Squared Error in MW: sqrt(mean((forecast - actual)^2))")
    bias: Optional[float] = Field(None, description="Forecast Bias (Mean Signed Error) in MW: mean(forecast - actual)")
    p50AbsoluteError: Optional[float] = Field(None, description="50th percentile (Median) of absolute error in MW")
    p90AbsoluteError: Optional[float] = Field(None, description="90th percentile of absolute error in MW")
    p95AbsoluteError: Optional[float] = Field(None, description="95th percentile of absolute error in MW")
    normalizedMaePct: Optional[float] = Field(None, description="Normalised MAE: (MAE / mean(actual)) * 100 (%)")
    meanActualGeneration: Optional[float] = Field(None, description="Mean actual generation in MW across matched intervals")
    maxOverforecast: Optional[ExtremeRecord] = Field(None, description="Single worst interval overforecast (highest positive error)")
    maxUnderforecast: Optional[ExtremeRecord] = Field(None, description="Single worst interval underforecast (most negative error)")
    p95OverforecastError: Optional[float] = Field(None, description="95th percentile overforecast in MW (suggested upside buffer)")
    p95UnderforecastError: Optional[float] = Field(None, description="95th percentile underforecast magnitude in MW (suggested thermal shortfall buffer)")
    matchedIntervals: int = Field(0, description="Number of valid intervals where both actual and forecast exist")
    totalIntervalsEvaluated: int = Field(0, description="Total delivery intervals evaluated in date range")
    overforecastCount: int = Field(0, description="Number of intervals where forecast > actual")
    underforecastCount: int = Field(0, description="Number of intervals where forecast < actual")
    exactMatchCount: int = Field(0, description="Number of intervals where forecast == actual")

class DataQualityReport(BaseModel):
    analysisPeriod: Dict[str, str] = Field(..., description="Requested start and end delivery dates")
    expectedDeliveryIntervals: int = Field(1488, description="Expected delivery intervals for Jan 2026 (48 periods * 31 days)")
    actualRecordsRetrieved: int = Field(..., description="Cleaned actual wind records from FUELHH")
    rawForecastRecordsRetrieved: int = Field(..., description="Cleaned forecast records from WINDFOR")
    uniqueForecastDeliveryIntervals: int = Field(..., description="Unique delivery intervals present in WINDFOR")
    matchedIntervals: int = Field(..., description="Successfully matched intervals with both actual and forecast")
    missingActualIntervals: int = Field(..., description="Delivery intervals lacking actual generation")
    missingForecastIntervals: int = Field(..., description="Delivery intervals lacking eligible forecast")
    actualCompletenessPct: float = Field(..., description="Actual generation completeness percentage")
    forecastCompletenessPct: float = Field(..., description="Eligible forecast completeness percentage")
    matchedCompletenessPct: float = Field(..., description="Matched completeness percentage")
    resolutionNotice: str = Field(..., description="Explanation of dataset time resolutions (FUELHH 30-min vs WINDFOR 60-min)")
    warnings: List[str] = Field(default_factory=list, description="Quality warnings and notices")
    cached: bool = Field(False, description="Whether data was served from local verified cache")
    cacheTimestamp: Optional[str] = Field(None, description="Timestamp of local cache creation")

class CutoffOption(BaseModel):
    id: str
    label: str
    description: str
    isDefault: bool = False
    group: str

class MethodologyInfo(BaseModel):
    selectionRule: str
    cutoffType: str
    cutoffDescription: str
    alignment: str
    unit: str = "MW"
    signConvention: str = "error = forecast - actual (Positive: Overforecast, Negative: Underforecast)"

class AnalysisResponse(BaseModel):
    period: Dict[str, str]
    methodology: MethodologyInfo
    metrics: AnalysisMetrics
    dataQuality: DataQualityReport
    records: List[MatchedRecord]

class VintageItem(BaseModel):
    publishTime: str
    generation: float
    leadHours: float
    isEligible: bool

class VintageResponse(BaseModel):
    deliveryTime: str
    actualGeneration: Optional[float]
    selectedForecast: Optional[WindforRecord]
    cutoffApplied: str
    totalVintages: int
    vintages: List[VintageItem]

class HorizonBucketResult(BaseModel):
    bucket: str = Field(..., description="Lead time bucket identifier, e.g. '0-6h', '6-12h'")
    label: str = Field(..., description="Human-readable label, e.g. '0-6h Ahead'")
    minLeadHours: float
    maxLeadHours: Optional[float] = None
    mae: Optional[float] = Field(None, description="Mean Absolute Error in MW")
    rmse: Optional[float] = Field(None, description="Root Mean Squared Error in MW")
    bias: Optional[float] = Field(None, description="Forecast Bias in MW")
    n: int = Field(..., description="Count of evaluated forecast-actual pairs")

class HorizonAnalysisResponse(BaseModel):
    period: Dict[str, str]
    alignment: str
    buckets: List[HorizonBucketResult]
    takeaway: str = Field(..., description="Plain-English takeaway summarizing horizon performance")
