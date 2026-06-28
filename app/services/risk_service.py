from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.db.models import Asset
from app.utils.rule_engine import evaluate_asset_group
from app.utils.validators import validate_post_generation
from app.services.context_builder import ContextBuilder
from app.chains import risk_chain
from app.schemas.responses import RiskResponse, RiskLevel, ConfidenceLevel
from app.schemas.requests import RiskRequest
import logging

logger = logging.getLogger(__name__)


class RiskService:
    def __init__(self, db: Session):
        self.db = db

    def calculate_risk(self, request: RiskRequest) -> RiskResponse:
        query = self.db.query(Asset).filter(Asset.id.in_(request.asset_ids))
        if request.tenant_id and request.tenant_id != "default":
            query = query.filter(Asset.tenant_id == request.tenant_id)
        assets = query.all()

        if not assets:
            raise HTTPException(status_code=404, detail="No matching assets found")

        logger.info(f"Generating risk assessment for {len(assets)} assets")
        # 1. Rule Engine Extracts Evidence
        evidence, risk_level = evaluate_asset_group(assets)

        # 2. Context Builder Normalizes, Compresses, and Specializes Context
        structured_context = ContextBuilder.build_risk_context(
            assets=assets, evidence=evidence
        )
        structured_context["risk_level"] = risk_level

        # 3. Invoke LangChain
        try:
            assessment_obj = risk_chain.evaluate_risk_chain(structured_context)
            assessment = assessment_obj.model_dump()
        except Exception as e:
            err_str = str(e).lower()
            is_rate_limit = (
                "429" in err_str or "quota" in err_str or "exhausted" in err_str
            )
            if is_rate_limit:
                logger.error("LLM Quota Exceeded during risk summary generation.")
            else:
                logger.error(f"LLM Failure in risk assessment: {e}", exc_info=True)
            # Deterministic Fallback Handling
            fallback_findings = []
            if len(evidence.get("expired_certificates", [])) > 0:
                fallback_findings.append(
                    f"{len(evidence['expired_certificates'])} expired certificate(s)"
                )
            if len(evidence.get("sensitive_services", [])) > 0:
                fallback_findings.append(
                    f"Exposed services: {', '.join(evidence['sensitive_services'])}"
                )
            if len(evidence.get("stale_assets", [])) > 0:
                fallback_findings.append(
                    f"{len(evidence['stale_assets'])} stale asset(s)"
                )

            assessment = {
                "risk_level": risk_level,
                "summary": "Fallback: LLM summary unavailable.",
                "findings": fallback_findings or ["No high risk findings detected."],
                "recommendations": ["Review backend findings for details."],
                "confidence": "LOW",
                "fallback": True,
            }

        # 4. Post-Generation Validation
        validated_assessment = validate_post_generation(assessment, structured_context)

        return RiskResponse.model_validate(validated_assessment)
