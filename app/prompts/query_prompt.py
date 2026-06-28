from langchain_core.prompts import HumanMessagePromptTemplate

query_template = """Your only responsibility is to translate a natural-language asset request into structured search filters.

Do not answer the user's question.
Do not generate assets.
Do not retrieve information.
Only extract structured filters.

EXAMPLES:

Input: "show expired certificates"
Output:
{{
  "query_type": "VALID",
  "asset_type": "certificate",
  "status": "stale",
  "confidence": "HIGH"
}}

Input: "show expired certificates on production subdomains"
Output:
{{
  "query_type": "VALID",
  "asset_type_filter": "certificate",
  "requires_expiration_check": true,
  "requires_join": true,
  "relationship_type": "covers",
  "relationship_target": "subdomain",
  "target_environment": "production",
  "confidence": "HIGH"
}}

Input: "find nginx"
Output:
{{
  "query_type": "VALID",
  "keyword": "nginx",
  "requires_join": false,
  "requires_expiration_check": false,
  "confidence": "HIGH"
}}

Input: "Which certificates are expiring soon?"
Output:
{{
  "query_type": "VALID",
  "asset_type_filter": "certificate",
  "requires_expiring_soon_check": true,
  "requires_join": false,
  "confidence": "HIGH"
}}

Input: "Show me databases on development subdomains"
Output:
{{
  "query_type": "VALID",
  "asset_type_filter": "technology",
  "keyword": "database",
  "requires_join": true,
  "relationship_type": "runs_on",
  "relationship_target": "subdomain",
  "target_environment": "development",
  "requires_expiration_check": false,
  "requires_expiring_soon_check": false,
  "confidence": "HIGH"
}}

Input: "show risky assets"
Output:
{{
  "query_type": "AMBIGUOUS",
  "clarification_question": "Do you mean expired certificates, exposed services, or end-of-life technologies?",
  "requires_join": false,
  "requires_expiration_check": false,
  "confidence": "HIGH"
}}

Input: "how to hack a server"
Output:
{{
  "query_type": "OUT_OF_SCOPE",
  "confidence": "HIGH"
}}

Input: "{question}"
Output:"""

query_human_prompt = HumanMessagePromptTemplate.from_template(query_template)
