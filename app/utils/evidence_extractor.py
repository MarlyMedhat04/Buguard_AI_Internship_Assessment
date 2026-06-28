from typing import Dict, Any
from app.db.models import Asset

def extract_evidence(asset: Asset) -> Dict[str, Any]:
    """Deterministically extracts evidence from an asset to minimize LLM context size."""
    evidence = {}
    
    # 1. Base properties
    evidence["asset_type"] = asset.type.value if hasattr(asset.type, 'value') else str(asset.type)
    evidence["value"] = asset.value
    
    if asset.tags:
        evidence["tags"] = list(asset.tags)
        
    # 2. Metadata parsing
    metadata = dict(asset.metadata_json) if asset.metadata_json else {}
    
    if "hostname" in metadata:
        evidence["hostname"] = metadata["hostname"]
    elif asset.type.name in ["domain", "subdomain"]:
        evidence["hostname"] = asset.value
        
    if "banner" in metadata:
        evidence["service_banner"] = metadata["banner"]
        
    if "ports" in metadata:
        evidence["ports"] = metadata["ports"]
        
    if "protocols" in metadata:
        evidence["protocols"] = metadata["protocols"]
        
    if "technology" in metadata or "technologies" in metadata:
        evidence["technologies"] = metadata.get("technologies", metadata.get("technology"))
        
    if asset.type.name == "certificate":
        evidence["certificate_present"] = True
        
    return evidence
