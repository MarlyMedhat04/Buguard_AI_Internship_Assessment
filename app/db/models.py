from sqlalchemy import (
    Column,
    String,
    DateTime,
    JSON,
    Enum,
    ForeignKey,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship
import uuid
import enum
from .database import Base
from datetime import datetime, timezone


class AssetType(str, enum.Enum):
    domain = "domain"
    subdomain = "subdomain"
    ip_address = "ip_address"
    service = "service"
    certificate = "certificate"
    technology = "technology"


class AssetStatus(str, enum.Enum):
    active = "active"
    stale = "stale"
    archived = "archived"
    expired = "expired"


class Asset(Base):
    __tablename__ = "assets"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, nullable=False, index=True, default="default")
    type = Column(Enum(AssetType), nullable=False, index=True)
    value = Column(String, nullable=False, index=True)
    status = Column(Enum(AssetStatus), nullable=False, default=AssetStatus.active)
    source = Column(String, nullable=False)
    tags = Column(JSON, default=list)
    metadata_json = Column(MutableDict.as_mutable(JSON), default=dict)
    first_seen = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    last_seen = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    outgoing_relationships = relationship(
        "Relationship",
        foreign_keys="Relationship.source_asset_id",
        back_populates="source_asset",
        cascade="all, delete-orphan",
    )
    incoming_relationships = relationship(
        "Relationship",
        foreign_keys="Relationship.target_asset_id",
        back_populates="target_asset",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "value", name="uix_tenant_asset_value"),
    )


class Relationship(Base):
    __tablename__ = "relationships"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(String, nullable=False, index=True, default="default")
    source_asset_id = Column(
        String, ForeignKey("assets.id"), nullable=False, index=True
    )
    target_asset_id = Column(
        String, ForeignKey("assets.id"), nullable=False, index=True
    )
    relationship_type = Column(String, nullable=False)

    source_asset = relationship(
        "Asset", foreign_keys=[source_asset_id], back_populates="outgoing_relationships"
    )
    target_asset = relationship(
        "Asset", foreign_keys=[target_asset_id], back_populates="incoming_relationships"
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "source_asset_id",
            "target_asset_id",
            "relationship_type",
            name="uix_tenant_relationship",
        ),
    )
