from app.chains.query_chain import QueryIntent
from app.db.models import AssetType, AssetStatus

def validate_query_intent(intent: QueryIntent) -> QueryIntent:
    """Validates the LLM output before SQL generation."""
    
    if intent.query_type in ["AMBIGUOUS", "OUT_OF_SCOPE"]:
        return intent
        
    # Validate asset_type enum
    if intent.asset_type_filter:
        valid_types = [e.value for e in AssetType]
        if intent.asset_type_filter.lower() not in valid_types:
            # Strip hallucinated type
            intent.asset_type_filter = None
            
    # Validate target_asset_type enum
    if getattr(intent, "relationship_target", None):
        valid_types = [e.value for e in AssetType]
        if intent.relationship_target.lower() not in valid_types:
            intent.relationship_target = None

    # Validate status enum
    if intent.status:
        valid_statuses = [e.value for e in AssetStatus]
        if intent.status.lower() not in valid_statuses:
            intent.status = None
            
    # Prevent empty valid queries (if it missed everything but said VALID)
    has_filter = any([
        intent.asset_type_filter, intent.status, intent.keyword,
        intent.environment_filter, intent.criticality_filter, intent.tag,
        intent.requires_join, intent.requires_expiration_check,
        intent.requires_expiring_soon_check
    ])
    
    if intent.query_type == "VALID" and not has_filter:
        intent.query_type = "AMBIGUOUS"
        intent.clarification_question = "I could not extract any specific filters. Could you rephrase your search?"
        
    return intent
