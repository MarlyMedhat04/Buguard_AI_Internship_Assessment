import asyncio
from app.db.database import SessionLocal, engine, Base
from app.db.models import Asset, Relationship, AssetType, AssetStatus
from app.chains.query_chain import QueryIntent
from app.utils.sql_builder import build_asset_query
import uuid

def setup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    # clean
    db.query(Relationship).delete()
    db.query(Asset).delete()
    db.commit()
    
    cert = Asset(
        id="cert_1", tenant_id="tenant_A", type=AssetType.certificate, value="cert.com", status=AssetStatus.expired, source="scan",
        tags=[], metadata_json={"expires": "2023-01-01"}
    )
    sub = Asset(
        id="sub_1", tenant_id="tenant_A", type=AssetType.subdomain, value="api.cert.com", status=AssetStatus.active, source="scan",
        tags=["prod"], metadata_json={}
    )
    db.add_all([cert, sub])
    db.commit()
    
    rel = Relationship(tenant_id="tenant_A", source_asset_id=cert.id, target_asset_id=sub.id, relationship_type="covers")
    db.add(rel)
    db.commit()
    
    return db

db = setup()
intent = QueryIntent(
    query_type="VALID",
    asset_type="certificate",
    status="expired",
    target_asset_type="subdomain",
    target_environment="prod",
    confidence="HIGH"
)
base_query = db.query(Asset).filter(Asset.tenant_id == "tenant_A")
q = build_asset_query(base_query, intent)
res = q.all()
print("MATCHES:", [a.id for a in res])
