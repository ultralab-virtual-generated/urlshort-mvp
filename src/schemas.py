from typing import Optional
from pydantic import BaseModel, HttpUrl, Field

class ShortenRequest(BaseModel):
    url: HttpUrl = Field(..., description="Long URL to shorten")
    custom_code: str | None = Field(None, description="Optional custom code")

class ShortenResponse(BaseModel):
    code: str
    short_url: str
    long_url: str

class StatsResponse(BaseModel):
    code: str
    long_url: str
    total_clicks: int
    last_access: Optional[str] = None
    recent: list[dict]
