from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.db.models import AssetType, AssetStatus

class AssetBase(BaseModel):
    id: Optional[str] = None
    type: AssetType
    value: str = ""
    status: AssetStatus = AssetStatus.active
    source: Optional[str] = "manual"
    tags: List[str] = Field(default_factory=list)
    metadata_json: Dict[str, Any] = Field(default_factory=dict, alias="metadata")
    
    model_config = ConfigDict(populate_by_name=True)

class AssetCreate(AssetBase):
    pass

class AssetResponse(AssetBase):
    first_seen: datetime
    last_seen: datetime
    tenant_id: str

    model_config = ConfigDict(from_attributes=True)

class ImportResult(BaseModel):
    imported: int
    updated: int
    failed: int
    assets_processed: int = 0
    errors: List[Dict[str, Any]] = Field(default_factory=list)

class RelationshipCreate(BaseModel):
    source: str
    target: str
    type: str = "related_to"
