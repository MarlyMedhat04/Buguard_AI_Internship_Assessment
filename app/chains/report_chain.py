from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from typing import Literal, List
import os
import json
from app.prompts.base_system_prompt import base_system_prompt
from app.prompts.report_prompt import report_human_prompt


class ReportResult(BaseModel):
    title: str = Field(..., description="Report title")
    executive_summary: str = Field(..., description="Brief executive summary")
    key_findings: List[str] = Field(
        ..., description="List of factual findings citing exact numbers"
    )
    recommendations: List[str] = Field(
        ..., description="List of actionable recommendations"
    )
    overall_risk: Literal["LOW", "MEDIUM", "HIGH"] = Field(
        ..., description="Overall risk assessment"
    )
    confidence: Literal["HIGH", "MEDIUM", "LOW"] = Field(
        ..., description="Confidence in the report"
    )


chat_prompt = ChatPromptTemplate.from_messages(
    [base_system_prompt, report_human_prompt]
)

from app.config import settings


def evaluate_report_chain(structured_context: dict) -> ReportResult:
    llm = ChatGoogleGenerativeAI(
        model=settings.MODEL_NAME, google_api_key=settings.GOOGLE_API_KEY
    )
    structured_llm = llm.with_structured_output(ReportResult)
    chain = chat_prompt | structured_llm

    return chain.invoke(
        {"structured_context": json.dumps(structured_context, indent=2)}
    )
