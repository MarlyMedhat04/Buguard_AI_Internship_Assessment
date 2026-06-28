from fastapi import APIRouter, Depends, Body, HTTPException
from typing import List, Any, Dict
from pydantic import BaseModel
import logging

from app.schemas.asset import ImportResult
from app.dependencies import get_import_service
from app.services.import_service import ImportService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/import", tags=["import"])


class ImportPayload(BaseModel):
    tenant_id: str = "default"
    assets: List[Dict[str, Any]] = []
    relationships: List[Dict[str, Any]] = []


@router.post("", response_model=ImportResult)
def import_assets(
    payload: ImportPayload = Body(...),
    import_service: ImportService = Depends(get_import_service),
):
    try:
        return import_service.process_import(
            payload.assets, payload.relationships, payload.tenant_id
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error during import: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
