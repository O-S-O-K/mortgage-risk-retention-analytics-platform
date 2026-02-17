from pydantic import BaseModel, Field


class CapacityOptimizationRequest(BaseModel):
    daily_applications: int = Field(gt=0, le=20000)
    review_capacity_per_underwriter: int = Field(gt=0, le=500)
    current_underwriters: int = Field(gt=0, le=500)
    max_underwriters: int = Field(gt=0, le=1000)
    min_threshold: float = Field(ge=0.4, le=0.9)
    max_threshold: float = Field(ge=0.4, le=0.95)
    step: float = Field(gt=0, le=0.1)


class CapacityScenario(BaseModel):
    threshold: float
    expected_manual_reviews: int
    required_underwriters: int
    excess_or_shortfall: int
    captured_high_risk_rate: float


class CapacityOptimizationResponse(BaseModel):
    recommended_threshold: float
    recommended_underwriters: int
    scenarios: list[CapacityScenario]
