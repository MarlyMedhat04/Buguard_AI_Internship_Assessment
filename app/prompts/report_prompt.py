from langchain_core.prompts import HumanMessagePromptTemplate

report_template = """Your task is to generate a structured JSON report summarizing the provided database statistics.

RULES:
1. ONLY use the supplied statistics.
2. Never invent numbers, assets, or findings.
3. Every finding MUST originate from the supplied statistics. 
4. Do not estimate counts.
5. Provide actionable recommendations based on the data.

EXAMPLES:

Input Statistics:
total_assets: 100
stale_assets_count: 5
expired_certificates: 2
expiring_certificates: 0

Output:
{{
  "title": "Asset Inventory Summary",
  "executive_summary": "The inventory contains 100 assets. There are several risks identified including stale assets and expired certificates.",
  "key_findings": [
    "Total Assets: 100",
    "Stale Assets: 5",
    "Expired Certificates: 2"
  ],
  "recommendations": [
    "Renew the 2 expired certificates immediately.",
    "Investigate the 5 stale assets."
  ],
  "overall_risk": "HIGH",
  "confidence": "HIGH"
}}

Input Statistics:
{structured_context}

Output:"""

report_human_prompt = HumanMessagePromptTemplate.from_template(report_template)
