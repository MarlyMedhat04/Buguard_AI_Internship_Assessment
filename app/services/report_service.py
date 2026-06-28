from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.models import Asset, AssetType, AssetStatus
from app.services.context_builder import ContextBuilder
from app.chains import report_chain
from app.services.report_validator import validate_report_result
from app.utils.markdown_builder import build_markdown_report
from app.schemas.responses import ReportResponse
from datetime import datetime, timezone, timedelta
import logging

logger = logging.getLogger(__name__)


class ReportService:
    def __init__(self, db: Session):
        self.db = db

    def generate_report(
        self, tenant_id: str, expiring_days_threshold: int = 30
    ) -> ReportResponse:
        logger.info(f"Generating report for tenant {tenant_id}")
        base_query = self.db.query(Asset).filter(Asset.tenant_id == tenant_id)

        total_assets = base_query.count()

        type_counts = (
            self.db.query(Asset.type, func.count(Asset.id))
            .filter(Asset.tenant_id == tenant_id)
            .group_by(Asset.type)
            .all()
        )
        type_stats = {}
        for t, count in type_counts:
            type_str = t.value if hasattr(t, "value") else str(t)
            type_stats[type_str] = count

        stale_count = base_query.filter(Asset.status == AssetStatus.stale).count()

        # Extract certificate dates deterministically
        certificates = base_query.filter(Asset.type == AssetType.certificate).all()
        cert_count = len(certificates)
        expired_cert_count = 0
        expiring_cert_count = 0

        now = datetime.now(timezone.utc)
        threshold_date = now + timedelta(days=expiring_days_threshold)

        for cert in certificates:
            expiry = cert.metadata_json.get("expiry_date")
            if expiry:
                try:
                    exp_date = datetime.fromisoformat(expiry.replace("Z", "+00:00"))
                    if exp_date < now:
                        expired_cert_count += 1
                    elif exp_date <= threshold_date:
                        expiring_cert_count += 1
                except ValueError:
                    pass

        high_risk_assets = stale_count + expired_cert_count

        raw_stats = {
            "total_assets": total_assets,
            "counts_by_type": type_stats,
            "stale_assets_count": stale_count,
            "certificates_count": cert_count,
            "expired_certificates": expired_cert_count,
            "expiring_certificates": expiring_cert_count,
            "high_risk_assets": high_risk_assets,
        }

        # Context Builder normalizes and injects metadata
        context = ContextBuilder.build_report_context(raw_stats)

        try:
            report_obj = report_chain.evaluate_report_chain(context)
            validated_result = validate_report_result(report_obj, raw_stats)
        except Exception as e:
            logger.error(f"LLM Failure in report generation: {e}")
            # Deterministic Fallback ensuring API stability
            validated_result = report_chain.ReportResult(
                title="Asset Inventory Fallback Report",
                executive_summary="Automated fallback report due to LLM processing failure.",
                key_findings=[
                    f"Total Assets: {total_assets}",
                    f"Stale Assets: {stale_count}",
                    f"Expired Certificates: {expired_cert_count}",
                ],
                recommendations=["Review high-risk assets immediately."],
                overall_risk="HIGH" if high_risk_assets > 0 else "LOW",
                confidence="LOW",
            )

        report_md = build_markdown_report(validated_result, context)
        return ReportResponse(tenant_id=tenant_id, report=report_md)
