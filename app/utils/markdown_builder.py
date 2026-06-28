from app.chains.report_chain import ReportResult
from typing import Dict, Any
import json

def build_markdown_report(result: ReportResult, context: Dict[str, Any]) -> str:
    """Converts the structured ReportResult JSON into formatted Markdown, appending metadata."""
    
    md_lines = []
    
    md_lines.append(f"# {result.title}")
    md_lines.append("")
    md_lines.append(f"**Overall Risk:** {result.overall_risk}")
    md_lines.append(f"**Confidence:** {result.confidence}")
    md_lines.append("")
    md_lines.append("## Executive Summary")
    md_lines.append(result.executive_summary)
    md_lines.append("")
    
    md_lines.append("## Key Findings")
    for finding in result.key_findings:
        md_lines.append(f"- {finding}")
    md_lines.append("")
    
    md_lines.append("## Recommendations")
    for rec in result.recommendations:
        md_lines.append(f"- {rec}")
    md_lines.append("")
    
    md_lines.append("---")
    md_lines.append("### AI Metadata")
    
    metadata = context.get("metadata", {})
    metadata_block = {
        "generated_at": metadata.get("generated_at"),
        "context_version": metadata.get("context_version"),
        "prompt_version": "v1",
        "model": "gemini-flash-latest"
    }
    
    md_lines.append("```json")
    md_lines.append(json.dumps(metadata_block, indent=2))
    md_lines.append("```")
    
    return "\n".join(md_lines)
