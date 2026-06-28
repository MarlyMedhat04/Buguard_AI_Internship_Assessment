from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.models import Relationship


def create_relationship(db: Session, relationship: Relationship) -> Relationship:
    db.add(relationship)
    db.flush()
    return relationship


def get_relationship(
    db: Session, source_id: str, target_id: str, relationship_type: str, tenant_id: str
) -> Optional[Relationship]:
    return (
        db.query(Relationship)
        .filter(
            Relationship.source_asset_id == source_id,
            Relationship.target_asset_id == target_id,
            Relationship.relationship_type == relationship_type,
            Relationship.tenant_id == tenant_id,
        )
        .first()
    )


def list_relationships(
    db: Session, tenant_id: str, skip: int = 0, limit: int = 100
) -> List[Relationship]:
    return (
        db.query(Relationship)
        .filter(Relationship.tenant_id == tenant_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
