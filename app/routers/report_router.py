from fastapi import APIRouter, Depends, HTTPException
from app.schemas.responses import ReportResponse
from app.dependencies import get_report_service
from app.services.report_service import ReportService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/report",
    tags=["report"]
)

@router.get("/{tenant_id}", response_model=ReportResponse)
def get_report(
    tenant_id: str,
    report_service: ReportService = Depends(get_report_service)
):
    try:
        return report_service.generate_report(tenant_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in get_report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("", response_model=ReportResponse)
def create_report(
    payload: dict,
    report_service: ReportService = Depends(get_report_service)
):
    tenant_id = payload.get("tenant_id", "default")
    try:
        return report_service.generate_report(tenant_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in create_report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
