from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.import_service import ImportService
from app.services.query_service import QueryService
from app.services.risk_service import RiskService
from app.services.enrich_service import EnrichService
from app.services.report_service import ReportService

def get_import_service(db: Session = Depends(get_db)) -> ImportService:
    return ImportService(db)

def get_query_service(db: Session = Depends(get_db)) -> QueryService:
    return QueryService(db)

def get_risk_service(db: Session = Depends(get_db)) -> RiskService:
    return RiskService(db)

def get_enrich_service(db: Session = Depends(get_db)) -> EnrichService:
    return EnrichService(db)

def get_report_service(db: Session = Depends(get_db)) -> ReportService:
    return ReportService(db)
