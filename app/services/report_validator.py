from app.chains.report_chain import ReportResult
from typing import Dict, Any
import re

def validate_report_result(result: ReportResult, db_stats: Dict[str, Any]) -> ReportResult:
    """
    Validates the LLM output against the ground truth database statistics.
    It corrects hallucinated numbers using the database as the ultimate source of truth.
    """
    truth_map = {
        "stale": db_stats.get("stale_assets_count", 0),
        "expired": db_stats.get("expired_certificates", 0),
        "expiring": db_stats.get("expiring_certificates", 0),
        "total": db_stats.get("total_assets", 0)
    }
    
    corrected_findings = []
    
    for finding in result.key_findings:
        lower_finding = finding.lower()
        
        if "stale" in lower_finding:
            finding = re.sub(r'\b\d+\b', str(truth_map["stale"]), finding)
        elif "expired" in lower_finding and "certificate" in lower_finding:
            finding = re.sub(r'\b\d+\b', str(truth_map["expired"]), finding)
        elif "expiring" in lower_finding:
            finding = re.sub(r'\b\d+\b', str(truth_map["expiring"]), finding)
        elif "total" in lower_finding:
            finding = re.sub(r'\b\d+\b', str(truth_map["total"]), finding)
            
        corrected_findings.append(finding)
        
    result.key_findings = corrected_findings
    
    return result
