from fastapi import APIRouter, Depends, HTTPException
from app.schemas.requests import EnrichRequest
from app.schemas.responses import EnrichResponse
from app.dependencies import get_enrich_service
from app.services.enrich_service import EnrichService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/enrich", tags=["enrich"])


@router.post("", response_model=EnrichResponse)
def enrich_asset(
    request: EnrichRequest, enrich_service: EnrichService = Depends(get_enrich_service)
):
    try:
        return enrich_service.process_enrichment(request)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in enrich_asset: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
