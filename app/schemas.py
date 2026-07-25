from pydantic import BaseModel, HttpUrl
from typing import Optional

class AuditRequest(BaseModel):
    url: HttpUrl

class AuditResult(BaseModel):
    url: str
    status: int
    response_time_ms: float
    title: str
    meta_description: Optional[str] = "N/A"
    page_size_bytes: int
    timestamp: str

class AuditResponse(BaseModel):
    source: str  # "live" or "cache"
    data: AuditResult

class ErrorDetail(BaseModel):
    code: str
    message: str