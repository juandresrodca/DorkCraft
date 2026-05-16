"""
Pydantic schemas for DorkCraft API request/response models.
Typed contracts make the API self-documenting and easy to extend.
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class GenerateRequest(BaseModel):
    """Incoming payload from the frontend."""
    query: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Natural language description of what the user wants to find.",
        examples=["Find PDF books about Linux malware analysis"]
    )


class DorkResponse(BaseModel):
    """Successful dork generation response."""
    dork: str = Field(..., description="The primary Google dork query string.")
    explanation: List[str] = Field(
        ..., description="Human-readable explanations for each operator used."
    )
    variations: List[str] = Field(
        ..., description="Alternative dork queries for the same intent."
    )
    category: Optional[str] = Field(
        None, description="Detected intent category (e.g., 'documents', 'people')."
    )
    warnings: List[str] = Field(
        default_factory=list, description="Validation warnings (length, deprecated operators, etc.)"
    )
    is_valid: bool = Field(
        True, description="Whether the dork is likely to work in Google."
    )


class ErrorResponse(BaseModel):
    """Returned when a query is refused or cannot be processed."""
    error: str
