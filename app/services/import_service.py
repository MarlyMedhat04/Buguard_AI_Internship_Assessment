import logging
import uuid
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import ValidationError
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.orm.attributes import flag_modified

from app.schemas.asset import AssetCreate, ImportResult, RelationshipCreate
from app.db.models import Asset, Relationship, AssetStatus
from app.db.repository import get_asset_by_value, create_asset, update_asset
from app.db.relationship_repository import create_relationship, get_relationship
from app.db.repository import get_asset_by_value, get_asset, create_asset, update_asset

logger = logging.getLogger(__name__)

class ImportService:
    def __init__(self, db: Session):
        self.db = db

    def process_import(self, assets_raw: List[Dict[str, Any]], relationships_raw: List[Dict[str, Any]], tenant_id: str) -> ImportResult:
        imported = 0
        updated = 0
        failed = 0
        errors = []

        logger.info(f"Starting import for tenant {tenant_id} with {len(assets_raw)} assets and {len(relationships_raw)} relationships")

        # Process Assets
        for i, item in enumerate(assets_raw):
            item_id = item.get("id") or item.get("value") or f"index_{i}"
            try:
                asset_in = AssetCreate.model_validate(item)
                
                with self.db.begin_nested():
                    existing = None
                    if asset_in.id:
                        existing = get_asset(self.db, asset_in.id, tenant_id)
                    if not existing and asset_in.value:
                        existing = get_asset_by_value(self.db, asset_in.value, tenant_id)
                    if existing:
                        # Merge Strategy
                        merged_meta = {**(existing.metadata_json or {})}
                        if asset_in.metadata_json:
                            merged_meta.update(asset_in.metadata_json)
                        existing.metadata_json = merged_meta
                        flag_modified(existing, "metadata_json")
                        
                        # Tag merge
                        if asset_in.tags:
                            existing.tags = list(set((existing.tags or []) + asset_in.tags))
                            
                        # Stale -> Active transition
                        if existing.status == AssetStatus.stale and asset_in.status == AssetStatus.active:
                            existing.status = AssetStatus.active
                        
                        # Update lifecycle (first_seen remains untouched)
                        existing.last_seen = datetime.now(timezone.utc)
                        
                        update_asset(self.db, existing)
                        updated += 1
                    else:
                        new_asset = Asset(
                            id=asset_in.id if asset_in.id else str(uuid.uuid4()),
                            tenant_id=tenant_id,
                            type=asset_in.type,
                            value=asset_in.value,
                            status=asset_in.status,
                            source=asset_in.source,
                            metadata_json=asset_in.metadata_json,
                            tags=asset_in.tags,
                            first_seen=datetime.now(timezone.utc),
                            last_seen=datetime.now(timezone.utc)
                        )
                        create_asset(self.db, new_asset)
                        imported += 1

            except ValidationError as e:
                failed += 1
                errors.append({"item_id": item_id, "error": str(e.errors())})
                logger.warning(f"Validation error for asset {item_id}: {e.errors()}")
            except IntegrityError as e:
                # Fallback if concurrent insert happens (UniqueConstraint triggers)
                failed += 1
                errors.append({"item_id": item_id, "error": "Duplicate entry constraint violation"})
                logger.error(f"IntegrityError processing asset {item_id}: {str(e)}")
            except SQLAlchemyError as e:
                failed += 1
                errors.append({"item_id": item_id, "error": "Database error"})
                logger.error(f"SQLAlchemy error processing asset {item_id}: {str(e)}")
            except ValueError as e:
                failed += 1
                errors.append({"item_id": item_id, "error": str(e)})
                logger.error(f"Value error processing asset {item_id}: {str(e)}")
            except Exception as e:
                failed += 1
                errors.append({"item_id": item_id, "error": str(e)})
                logger.error(f"Unexpected error processing asset {item_id}: {str(e)}")

        # Process Relationships
        for i, rel_item in enumerate(relationships_raw):
            item_id = f"rel_index_{i}"
            try:
                rel_in = RelationshipCreate.model_validate(rel_item)
                
                with self.db.begin_nested():
                    source = get_asset(self.db, rel_in.source, tenant_id) or get_asset_by_value(self.db, rel_in.source, tenant_id)
                    target = get_asset(self.db, rel_in.target, tenant_id) or get_asset_by_value(self.db, rel_in.target, tenant_id)
                    
                    if source and target:
                        existing_rel = get_relationship(self.db, source.id, target.id, rel_in.type, tenant_id)
                        if not existing_rel:
                            new_rel = Relationship(
                                tenant_id=tenant_id,
                                source_asset_id=source.id,
                                target_asset_id=target.id,
                                relationship_type=rel_in.type
                            )
                            create_relationship(self.db, new_rel)
                    else:
                        failed += 1
                        errors.append({"item_id": rel_in.source, "error": "Source or target asset not found"})
                        logger.warning(f"Relationship skipped: Source '{rel_in.source}' or Target '{rel_in.target}' not found")
                        
            except ValidationError as e:
                failed += 1
                errors.append({"item_id": item_id, "error": str(e.errors())})
                logger.warning(f"Validation error for relationship {i}: {e.errors()}")
            except IntegrityError as e:
                failed += 1
                errors.append({"item_id": item_id, "error": "Relationship already exists"})
                logger.warning(f"Integrity error for relationship {i}: {str(e)}")
            except SQLAlchemyError as e:
                failed += 1
                errors.append({"item_id": item_id, "error": "Database error"})
                logger.error(f"SQLAlchemy error processing relationship {i}: {str(e)}")
            except ValueError as e:
                failed += 1
                errors.append({"item_id": item_id, "error": str(e)})
                logger.error(f"Value error processing relationship {i}: {str(e)}")
            except Exception as e:
                failed += 1
                errors.append({"item_id": item_id, "error": str(e)})
                logger.error(f"Unexpected error processing relationship {i}: {str(e)}")

        try:
            self.db.commit()
            logger.info(f"Successfully committed batch for tenant {tenant_id}")
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Failed to commit batch for tenant {tenant_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Database transaction failed")

        return ImportResult(
            imported=imported,
            updated=updated,
            failed=failed,
            errors=errors,
            assets_processed=imported + updated
        )
