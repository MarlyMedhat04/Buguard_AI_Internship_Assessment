from fastapi import APIRouter, Depends, HTTPException
from app.schemas.requests import RiskRequest
from app.schemas.responses import RiskResponse
from app.dependencies import get_risk_service
from app.services.risk_service import RiskService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/risk", tags=["risk"])


@router.post("", response_model=RiskResponse)
def calculate_risk(
    request: RiskRequest, risk_service: RiskService = Depends(get_risk_service)
):
    try:
        return risk_service.calculate_risk(request)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in calculate_risk: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
