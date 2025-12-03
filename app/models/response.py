"""
Response models for API endpoints.
"""
from typing import List
from pydantic import BaseModel, Field


class CVSummaryResponse(BaseModel):
    """Structured response model for CV summary."""
    
    summary: str = Field(..., description="Summary of the CV")
    skills: List[str] = Field(..., description="List of skills extracted from the CV")
    experience_years: float = Field(..., description="Total years of experience")
    
    class Config:
        json_schema_extra = {
            "example": {
                "summary": "Experienced software engineer with 5 years in full-stack development...",
                "skills": ["Python", "JavaScript", "React", "Node.js", "AWS"],
                "experience_years": 5.5
            }
        }


class ErrorResponse(BaseModel):
    """Error response model."""
    
    error: str = Field(..., description="Error message")
    detail: str = Field(default="", description="Additional error details")

