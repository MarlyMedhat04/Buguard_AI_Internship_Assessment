from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from typing import List, Literal
import os
import json
from app.prompts.base_system_prompt import base_system_prompt
from app.prompts.risk_prompt import risk_human_prompt

class RiskAssessment(BaseModel):
    risk_level: str = Field(..., description="The risk level provided by the backend")
    summary: str = Field(..., description="Executive summary")
    findings: List[str] = Field(default_factory=list, description="List of concise findings")
    recommendations: List[str] = Field(default_factory=list, description="Actionable recommendations")
    confidence: Literal["HIGH", "MEDIUM", "LOW"] = Field(..., description="Confidence in the assessment")

chat_prompt = ChatPromptTemplate.from_messages([
    base_system_prompt,
    risk_human_prompt
])

from app.config import settings

def evaluate_risk_chain(structured_context: dict) -> RiskAssessment:
    risk_level = structured_context.pop("risk_level", "unknown")
    llm = ChatGoogleGenerativeAI(model=settings.MODEL_NAME, google_api_key=settings.GOOGLE_API_KEY)
    structured_llm = llm.with_structured_output(RiskAssessment)
    chain = chat_prompt | structured_llm
    
    return chain.invoke({
        "structured_context": json.dumps(structured_context, indent=2),
        "risk_level": risk_level
    })
