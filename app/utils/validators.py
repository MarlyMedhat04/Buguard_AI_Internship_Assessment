from typing import Dict, Any
import re

def validate_post_generation(assessment: Dict[str, Any], structured_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates the LLM output against the grounded context.
    Removes findings/recommendations that reference unknown assets or technologies.
    """
    valid_findings = []
    
    known_asset_ids = {a["id"] for a in structured_context.get("assets", [])}
    
    # ID pattern matcher (e.g., looks for typical asset IDs like uuid or 'asset-')
    # For now, we check if the finding explicitly mentions an asset ID that is not in the context.
    
    for finding in assessment.get("findings", []):
        words = finding.split()
        is_hallucinated = False
        for word in words:
            clean_word = re.sub(r'[^a-zA-Z0-9-]', '', word)
            # If the LLM mentions an ID format (e.g. starts with 'a' followed by digits) not in the context
            if clean_word.startswith("asset-") or clean_word.startswith("a"):
                if any(char.isdigit() for char in clean_word):
                    if clean_word not in known_asset_ids:
                        is_hallucinated = True
                        break
        
        if not is_hallucinated:
            valid_findings.append(finding)
            
    assessment["findings"] = valid_findings
    
    return assessment
