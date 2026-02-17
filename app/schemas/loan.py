from pydantic import BaseModel, Field


class LoanRequest(BaseModel):
    credit_score: int = Field(ge=300, le=850)
    ltv: float = Field(ge=0, le=150)
    dti: float = Field(ge=0, le=100)
    days_in_processing: int = Field(ge=0, le=120)
    documentation_completeness_flag: int = Field(ge=0, le=1)
    income: float = Field(gt=0)
    loan_amount: float = Field(gt=0)
    interest_rate: float = Field(gt=0, le=30)
    tenure_years: int = Field(gt=0, le=40)
