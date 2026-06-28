from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import enum
from app.schemas.asset import AssetResponse

class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class ConfidenceLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class QueryResponse(BaseModel):
    query_type: str
    message: Optional[str] = None
    clarification_question: Optional[str] = None
    assets: List[AssetResponse] = Field(default_factory=list)
    intent: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    fallback_used: Optional[bool] = False

class RiskResponse(BaseModel):
    risk_level: RiskLevel
    summary: str
    confidence: ConfidenceLevel
    fallback: Optional[bool] = False

class EnrichResponse(BaseModel):
    enriched_assets: List[str] = Field(default_factory=list)
    errors: List[Dict[str, Any]] = Field(default_factory=list)

class ReportResponse(BaseModel):
    tenant_id: str
    report: str
