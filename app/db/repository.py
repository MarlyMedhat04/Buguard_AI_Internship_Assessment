from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.models import Asset
from datetime import datetime, timezone

def get_asset(db: Session, asset_id: str, tenant_id: str) -> Optional[Asset]:
    query = db.query(Asset).filter(Asset.id == asset_id)
    if tenant_id and tenant_id != "default":
        query = query.filter(Asset.tenant_id == tenant_id)
    return query.first()

def get_asset_by_value(db: Session, value: str, tenant_id: str) -> Optional[Asset]:
    return db.query(Asset).filter(Asset.value == value, Asset.tenant_id == tenant_id).first()

def list_assets(db: Session, tenant_id: str, skip: int = 0, limit: int = 100) -> List[Asset]:
    return db.query(Asset).filter(Asset.tenant_id == tenant_id).offset(skip).limit(limit).all()

def create_asset(db: Session, asset: Asset) -> Asset:
    db.add(asset)
    db.flush()
    return asset

def update_asset(db: Session, asset: Asset) -> Asset:
    db.add(asset)
    db.flush()
    return asset

def update_last_seen(db: Session, asset: Asset) -> Asset:
    asset.last_seen = datetime.now(timezone.utc)
    db.add(asset)
    db.flush()
    return asset
