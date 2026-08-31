from pydantic import BaseModel, validator
from typing import Optional

class PredictRequest(BaseModel):
    text:              str
    platform:          Optional[str]   = "facebook"
    account_age:       Optional[float] = 365.0
    posting_frequency: Optional[float] = 1.0
    session_id:        Optional[str]   = None

    @validator("text")
    def text_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("text cannot be empty")
        if len(v) > 2000:
            raise ValueError("text exceeds maximum length of 2000 characters")
        return v.strip()

    @validator("account_age")
    def age_must_be_positive(cls, v):
        if v is None: return 365.0
        return max(0.0, float(v))

    @validator("posting_frequency")
    def freq_must_be_positive(cls, v):
        if v is None: return 1.0
        return max(0.0, float(v))