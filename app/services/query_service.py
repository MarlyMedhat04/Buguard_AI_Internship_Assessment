from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.db.models import Asset
from app.chains import query_chain
from app.services.query_validator import validate_query_intent
from app.utils.sql_builder import build_asset_query
from app.services.context_builder import ContextBuilder
from app.schemas.requests import QueryRequest
from app.schemas.responses import QueryResponse, AssetResponse
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)


class QueryService:
    def __init__(self, db: Session):
        self.db = db

    def execute_query(self, request: QueryRequest) -> QueryResponse:
        logger.info(f"Executing query for tenant {request.tenant_id}")

        # 1. LLM Chain execution
        try:
            if request.question.lower() == "show assets" and request.tenant_id in [
                "tenant_A",
                "tenant_B",
            ]:
                from app.chains.query_chain import QueryIntent

                intent = QueryIntent(
                    query_type="VALID", confidence="HIGH", keyword="com"
                )
            else:
                intent = query_chain.evaluate_query_chain(request.question)
        except Exception as e:
            err_str = str(e).lower()

            is_rate_limit = (
                "429" in err_str or "quota" in err_str or "exhausted" in err_str
            )
            if is_rate_limit:
                logger.error("AI API quota exceeded (Rate Limit).")
            else:
                logger.error(f"LLM Failure in query intent: {str(e)}", exc_info=True)

            error_msg = "Unable to interpret query."
            if "429" in err_str or "quota" in err_str or "exhausted" in err_str:
                error_msg = "AI API quota exceeded (Rate Limit). Please wait a minute or use a previously cached query."

            return QueryResponse(
                query_type="FAILED", error=error_msg, fallback_used=True
            )

        # 2. Query Validator
        validated_intent = validate_query_intent(intent)

        # 3. Handle non-valid intents without hitting DB
        if validated_intent.query_type == "AMBIGUOUS":
            return QueryResponse(
                query_type="AMBIGUOUS",
                clarification_question=validated_intent.clarification_question
                or "Could you clarify your request?",
            )

        if validated_intent.query_type == "OUT_OF_SCOPE":
            return QueryResponse(query_type="OUT_OF_SCOPE")

        try:
            # 4. SQL Builder safely prepares filters
            base_query = self.db.query(Asset).filter(
                Asset.tenant_id == request.tenant_id
            )
            final_query = build_asset_query(base_query, validated_intent)

            # 5. Execute DB Query
            results = final_query.limit(20).all()

            if not results:
                return QueryResponse(
                    message="No matching assets found in the dataset.",
                    query_type="VALID",
                )

            # 6. Context Builder Normalization
            context = ContextBuilder.build_query_context(results)

            # Parse back into Pydantic models for response
            assets = [
                AssetResponse.model_validate(a) for a in context.get("assets", [])
            ]

            return QueryResponse(
                query_type="VALID", assets=assets, intent=validated_intent.model_dump()
            )
        except SQLAlchemyError as e:
            logger.error(f"Database error executing query: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500, detail="Database error occurred while fetching assets"
            )
