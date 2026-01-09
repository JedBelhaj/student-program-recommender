"""Pydantic models for API request/response validation."""

from typing import List, Optional
from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    """User profile for generating recommendations."""
    interests: str = Field(..., description="Comma-separated interests (e.g., 'technology, design, mathematics')")
    math_grade: float = Field(..., ge=0, le=100, description="Mathematics grade (0-100)")
    science_grade: float = Field(..., ge=0, le=100, description="Science grade (0-100)")
    language_grade: float = Field(..., ge=0, le=100, description="Language grade (0-100)")
    user_id: Optional[str] = Field(None, description="Existing user ID (for returning users)")


class Recommendation(BaseModel):
    """Single program recommendation with explanation."""
    program_id: str
    program_name: str
    description: str
    skills: str
    score: float
    explanation: str


class RecommendationResponse(BaseModel):
    """Response containing list of recommendations."""
    user_id: Optional[str] = None
    recommendations: List[Recommendation]
    approach: str = Field(..., description="content-based, collaborative, or hybrid")


class FeedbackRequest(BaseModel):
    """User feedback on a recommendation."""
    user_id: Optional[str] = None
    program_id: str
    feedback_type: str = Field(..., description="clicked, accepted, or rejected")
    session_id: Optional[str] = None
