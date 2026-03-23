"""
Pydantic request and response schemas for the timer API

Validation rules:
- 'hours', 'minutes' and 'seconds' must all be >= 0
- 'minutes' and 'seconds' must be <= 59
- 'url' must be a valid HTTP url

"""
from pydantic import BaseModel, HttpUrl, field_validator

class TimerCreateRequest(BaseModel):
    """
    Request body for POST /timer
    """
    url: HttpUrl
    hours: int = 0
    minutes: int = 0
    seconds: int = 0

    @field_validator("hours", "minutes", "seconds")
    @classmethod
    def non_negative(cls, v: int, info) -> int:
        """
        Reject negative values
        """
        if v < 0:
            raise ValueError(f"{info.field_name} must be >= 0")
        return v
    
    @field_validator("minutes", "seconds")
    @classmethod
    def max_59(cls, v: int, info) -> int:
        """
        Reject values above 59 for 'minutes' and 'seconds'
        """
        if v > 59:
            raise ValueError(f"{info.field_name} must be <= 59")
        return v
    
    def total_seconds(self) -> int:
        """
        Returns the total timer duration in seconds
        """
        return self.hours * 3600 + self.minutes * 60 + self.seconds


class TimerCreateResponse(BaseModel):
    """
    Response body for POST /timer
    """
    id: str
    time_left: int

class TimerStatusResponse(BaseModel):
    """
    Response body for GET /timer
    """
    id: str
    time_left: int