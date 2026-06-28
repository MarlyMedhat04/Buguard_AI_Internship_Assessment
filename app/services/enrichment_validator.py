from app.chains.enrich_chain import EnrichmentResult

def validate_enrichment_result(result: EnrichmentResult, asset_type: str) -> EnrichmentResult:
    """Validates the LLM output to prevent contradictory or hallucinated classifications."""
    
    # Validation 1: Asset Type constraints
    if asset_type.lower() == "certificate":
        if result.category != "certificate":
            result.category = "unknown"
            
    if asset_type.lower() in ["domain", "subdomain"]:
        if result.category in ["certificate", "technology"]:
            result.category = "unknown"
            
    # Validation 2: Ensure evidence is not empty if a confident classification is made
    has_classification = (
        result.environment != "unknown" or 
        result.criticality != "unknown" or 
        result.category != "unknown"
    )
    
    if has_classification and not result.evidence:
        result.confidence = "LOW"
        result.environment = "unknown"
        result.criticality = "unknown"
        result.category = "unknown"
        
    return result
