from pydantic import BaseModel, HttpUrl, field_validator

class TimerCreateRequest(BaseModel):
    url: HttpUrl
    hours: int = 0
    minutes: int = 0
    seconds: int = 0

    @field_validator("hours", "minutes", "seconds")
    @classmethod
    def non_negative(cls, v: int, info) -> int:
        if v < 0:
            raise ValueError(f"{info.field_name} must be >= 0")
        return v
    
    @field_validator("minutes", "seconds")
    @classmethod
    def max_59(cls, v: int, info) -> int:
        if v > 59:
            raise ValueError(f"{info.field_name} must be <= 59")
        return v
    
    def total_seconds(self) -> int:
        return self.hours * 3600 + self.minutes * 60 + self.seconds


class TimerCreateResponse(BaseModel):
    id: str
    time_left: int

class TimerStatusResponse(BaseModel):
    id: str
    time_left: int