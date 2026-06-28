from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from typing import Literal, List
import os
import json
from app.prompts.base_system_prompt import base_system_prompt
from app.prompts.enrichment_prompt import enrichment_human_prompt

class EnrichmentResult(BaseModel):
    environment: str = Field(..., description="The deployment environment (e.g. production, staging, development, unknown)")
    criticality: str = Field(..., description="The criticality of the asset (high, medium, low, unknown)")
    category: str = Field(..., description="The category of the asset (api, website, service, technology, certificate, infrastructure, unknown)")
    confidence: str = Field(..., description="Confidence reflecting evidence quality (HIGH, MEDIUM, LOW)")
    evidence: List[str] = Field(..., description="List of supporting evidence strings")

chat_prompt = ChatPromptTemplate.from_messages([
    base_system_prompt,
    enrichment_human_prompt
])

from app.config import settings

def evaluate_enrichment_chain(structured_context: dict) -> EnrichmentResult:
    llm = ChatGoogleGenerativeAI(model=settings.MODEL_NAME, google_api_key=settings.GOOGLE_API_KEY)
    structured_llm = llm.with_structured_output(EnrichmentResult)
    chain = chat_prompt | structured_llm
    
    return chain.invoke({
        "structured_context": json.dumps(structured_context, indent=2)
    })
