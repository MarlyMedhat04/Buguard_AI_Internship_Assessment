from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from app.schemas.requests import QueryRequest
from app.schemas.responses import QueryResponse
from app.dependencies import get_query_service
from app.services.query_service import QueryService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/query", tags=["query"])


@router.post("", response_model=QueryResponse)
def query_assets(
    request: QueryRequest, query_service: QueryService = Depends(get_query_service)
):
    try:
        return query_service.execute_query(request)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in query_assets: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
