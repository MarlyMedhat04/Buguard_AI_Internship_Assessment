from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from app.db.models import Asset, AssetType, AssetStatus
from app.db.repository import get_asset, update_asset, get_asset_by_value, create_asset
from app.utils.evidence_extractor import extract_evidence
from app.services.context_builder import ContextBuilder
from app.chains import enrich_chain
from app.services.enrichment_validator import validate_enrichment_result
from app.schemas.requests import EnrichRequest
from app.schemas.responses import EnrichResponse
from datetime import datetime, timezone
import logging
from sqlalchemy.orm.attributes import flag_modified
import uuid

logger = logging.getLogger(__name__)

class EnrichService:
    def __init__(self, db: Session):
        self.db = db

    def process_enrichment(self, request: EnrichRequest) -> EnrichResponse:
        logger.info(f"Enriching assets for tenant {request.tenant_id}")
        
        enriched_assets = []
        errors = []
        
        assets_to_enrich = []
        
        if request.asset_ids:
            for asset_id in request.asset_ids:
                asset = get_asset(self.db, asset_id, request.tenant_id)
                if asset:
                    assets_to_enrich.append(asset)
                else:
                    errors.append({"asset_id": asset_id, "error": "Asset not found"})
                    
        elif request.type and request.value:
            # On-the-fly enrichment
            asset = get_asset_by_value(self.db, request.value, request.tenant_id)
            if not asset:
                try:
                    asset_type = AssetType(request.type)
                except ValueError:
                    errors.append({"asset_id": request.value, "error": f"Invalid asset type: {request.type}"})
                    return EnrichResponse(enriched_assets=[], errors=errors)
                    
                asset = Asset(
                    id=str(uuid.uuid4()),
                    tenant_id=request.tenant_id,
                    type=asset_type,
                    value=request.value,
                    status=AssetStatus.active,
                    source="enrichment_api"
                )
                create_asset(self.db, asset)
            assets_to_enrich.append(asset)
        else:
            raise HTTPException(status_code=422, detail="Must provide either asset_ids or type and value")

        for asset in assets_to_enrich:
            try:
                # 1. Extract Evidence deterministically
                evidence = extract_evidence(asset)
                
                # 2. Build Context
                context = ContextBuilder.build_enrichment_context(asset=asset, evidence=evidence)
                
                # 3. Execute LangChain
                try:
                    enrichment_obj = enrich_chain.evaluate_enrichment_chain(context)
                    # 4. Validate output
                    asset_type_str = asset.type.value if hasattr(asset.type, 'value') else str(asset.type)
                    validated_enrichment = validate_enrichment_result(enrichment_obj, asset_type_str)
                    result_dict = validated_enrichment.model_dump()
                except Exception as e:
                    err_str = str(e).lower()
                    is_rate_limit = "429" in err_str or "quota" in err_str or "exhausted" in err_str
                    if is_rate_limit:
                        logger.error(f"LLM Quota Exceeded during enrichment for {asset.id}.")
                    else:
                        logger.error(f"LLM Failure in enrichment for {asset.id}: {str(e)}", exc_info=True)
                    # Deterministic Fallback
                    result_dict = {
                        "environment": "unknown",
                        "criticality": "unknown",
                        "category": "unknown",
                        "confidence": "LOW",
                        "evidence": [],
                        "fallback_used": True
                    }
                
                # 5. Metadata Envelope construction
                metadata = {**(asset.metadata_json or {})}
                
                ai_enrichment_envelope = {
                    "version": "1.0",
                    "model": "gemini-flash-latest",
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "prompt_version": "v1",
                    "confidence": result_dict.get("confidence", "LOW"),
                    "result": result_dict
                }
                
                metadata["ai_enrichment"] = ai_enrichment_envelope
                asset.metadata_json = metadata
                flag_modified(asset, "metadata_json")
                
                update_asset(self.db, asset)
                enriched_assets.append(asset.id)
                
            except Exception as e:
                logger.error(f"Unexpected error processing enrichment for {asset.id}: {e}")
                errors.append({"asset_id": asset.id, "error": str(e)})

        try:
            self.db.commit()
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Failed to commit enrichment batch: {e}")
            raise HTTPException(status_code=500, detail="Database transaction failed")
        
        return EnrichResponse(
            enriched_assets=enriched_assets,
            errors=errors
        )
