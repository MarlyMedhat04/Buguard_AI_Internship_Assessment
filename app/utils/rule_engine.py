from typing import List, Dict, Any, Tuple
from app.db.models import Asset, AssetType, AssetStatus
from datetime import datetime, timezone

class RuleEngine:
    @staticmethod
    def evaluate_assets(assets: List[Asset]) -> Dict[str, Any]:
        results = {
            "expired_certificates": [],
            "expiring_certificates": [],
            "sensitive_services": [],
            "end_of_life_technologies": [],
            "stale_assets": [],
            "missing_owners": []
        }
        
        now = datetime.now(timezone.utc)
        
        for asset in assets:
            # Stale
            if asset.status == "stale" or asset.status == AssetStatus.stale:
                results["stale_assets"].append(asset.value)
                
            # Certificates
            if asset.type == "certificate" or asset.type == AssetType.certificate:
                metadata = asset.metadata_json or {}
                expiry = metadata.get("expiry_date")
                if expiry:
                    try:
                        exp_date = datetime.fromisoformat(expiry.replace('Z', '+00:00'))
                        if exp_date < now:
                            results["expired_certificates"].append(asset.value)
                    except ValueError:
                        pass
                        
            # Sensitive Services
            if asset.type == "service" or asset.type == AssetType.service:
                metadata = asset.metadata_json or {}
                banner = metadata.get("banner", "").lower()
                for sensitive in ["ssh", "ftp", "telnet"]:
                    if sensitive in banner:
                        results["sensitive_services"].append(asset.value)
                        
            # EOL
            if asset.type == "technology" or asset.type == AssetType.technology:
                tech_val = asset.value.lower()
                if "apache 2.2" in tech_val or "php 5" in tech_val or "postgresql 9" in tech_val:
                    results["end_of_life_technologies"].append(asset.value)
                    
            # Missing Owner
            metadata = asset.metadata_json or {}
            tags = asset.tags or []
            has_owner = "owner" in metadata or any(t.lower().startswith("owner:") for t in tags)
            if not has_owner:
                results["missing_owners"].append(asset.value)

        return results

def evaluate_asset_group(assets: List[Asset]) -> Tuple[Dict[str, Any], str]:
    evidence = RuleEngine.evaluate_assets(assets)
    
    # Calculate overall risk
    overall_risk = "LOW"
    if len(evidence["stale_assets"]) > 0 or len(evidence["missing_owners"]) > 0:
        overall_risk = "MEDIUM"
    if len(evidence["expired_certificates"]) > 0 or len(evidence["sensitive_services"]) > 0 or len(evidence["end_of_life_technologies"]) > 0:
        overall_risk = "HIGH"
        
    return evidence, overall_risk
