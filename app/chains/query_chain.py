from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from typing import Optional, Literal
import os
from app.prompts.base_system_prompt import base_system_prompt
from app.prompts.query_prompt import query_human_prompt
import functools

class QueryIntent(BaseModel):
    query_type: Literal["VALID", "AMBIGUOUS", "OUT_OF_SCOPE"] = Field(..., description="Classification of the query")
    asset_type_filter: Optional[str] = Field(None, description="The primary type of asset to filter by (e.g. domain, subdomain, ip_address, service, certificate, technology)")
    status: Optional[str] = Field(None, description="The status of the asset, if mentioned")
    keyword: Optional[str] = Field(None, description="A keyword to search for")
    environment_filter: Optional[str] = Field(None, description="Environment filter (e.g. production, dev)")
    criticality_filter: Optional[str] = Field(None, description="Criticality filter (e.g. HIGH, MEDIUM, LOW)")
    tag: Optional[str] = Field(None, description="Tag mentioned")
    
    requires_join: bool = Field(False, description="True if a relationship traversal is required to answer the query")
    relationship_type: Optional[str] = Field(None, description="Type of relationship (e.g. covers, runs_on, resolves_to)")
    relationship_target: Optional[str] = Field(None, description="Target asset type of the relationship (e.g. subdomain, server)")
    target_environment: Optional[str] = Field(None, description="Environment of the related target asset")
    target_tag: Optional[str] = Field(None, description="Tag of the related target asset")
    
    requires_expiration_check: bool = Field(False, description="True if the user asked about expired assets")
    requires_expiring_soon_check: bool = Field(False, description="True if the user asked about assets expiring soon (e.g. next 30 days)")
    date_range: Optional[str] = Field(None, description="Date range if mentioned")
    sort: Optional[str] = Field(None, description="Field to sort by")
    limit: Optional[int] = Field(None, description="Limit of results to return")
    
    confidence: Literal["HIGH", "MEDIUM", "LOW"] = Field(..., description="Confidence level")
    clarification_question: Optional[str] = Field(None, description="Question to ask if ambiguous")

chat_prompt = ChatPromptTemplate.from_messages([
    base_system_prompt,
    query_human_prompt
])

from app.config import settings

@functools.lru_cache(maxsize=100)
def evaluate_query_chain(question: str) -> QueryIntent:
    llm = ChatGoogleGenerativeAI(
    model="gemini-flash-latest", 
    temperature=0
    )
    structured_llm = llm.with_structured_output(QueryIntent)
    chain = chat_prompt | structured_llm
    
    return chain.invoke({"question": question})