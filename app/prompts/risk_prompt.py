from langchain_core.prompts import HumanMessagePromptTemplate

risk_template = """Your task is to analyze the following structured context and generate a risk assessment.

Context:
{structured_context}

Calculated Risk Level: {risk_level}

Using ONLY the supplied grounded context:
1. Generate an executive summary of the assets.
2. Explain why the provided calculated risk level is appropriate.
3. Provide concise findings from the data.
4. Provide actionable recommendations based ONLY on the findings.

Do NOT recalculate the risk level. The backend has already determined it to be {risk_level}.
"""

risk_human_prompt = HumanMessagePromptTemplate.from_template(risk_template)
