from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(..., description="Natural language question to query assets")
    tenant_id: str = "default"


from typing import List, Optional


class RiskRequest(BaseModel):
    asset_ids: List[str]
    tenant_id: str = "default"


class EnrichRequest(BaseModel):
    asset_ids: Optional[List[str]] = Field(default_factory=list)
    type: Optional[str] = None
    value: Optional[str] = None
    tenant_id: str = "default"


class ReportRequest(BaseModel):
    tenant_id: str = "default"
