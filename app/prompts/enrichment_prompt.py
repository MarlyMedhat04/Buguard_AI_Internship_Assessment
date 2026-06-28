from langchain_core.prompts import HumanMessagePromptTemplate

enrichment_template = """Your task is to classify an IT asset using ONLY the supplied grounded asset context and evidence.

Classify the following:
- environment (production, staging, development, unknown)
- criticality (high, medium, low, unknown)
- category (api, website, service, technology, certificate, infrastructure, unknown)

RULES:
1. Explain your reasoning using explicit evidence from the asset.
2. Do not infer unsupported values.
3. If evidence is insufficient, return "unknown" and set confidence to "LOW".
4. Confidence should reflect the quality of the evidence, not your internal certainty.

EXAMPLES:

Input Context:
hostname: api.prod.example.com
service: HTTPS
technology: NGINX

Output:
{{
  "environment": "production",
  "criticality": "high",
  "category": "api",
  "confidence": "HIGH",
  "evidence": ["hostname contains 'prod'", "HTTPS service detected"]
}}

Input Context:
hostname: test.internal.local

Output:
{{
  "environment": "development",
  "criticality": "low",
  "category": "infrastructure",
  "confidence": "MEDIUM",
  "evidence": ["hostname contains 'test' and 'internal'"]
}}

Input Context:
type: certificate

Output:
{{
  "environment": "unknown",
  "criticality": "unknown",
  "category": "certificate",
  "confidence": "HIGH",
  "evidence": ["asset type is strictly certificate"]
}}

Input Context:
{structured_context}

Output:"""

enrichment_human_prompt = HumanMessagePromptTemplate.from_template(enrichment_template)
