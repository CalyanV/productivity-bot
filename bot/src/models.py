from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ParsedTask(BaseModel):
    """Structured task data from NLP parsing"""

    title: str = Field(description="Clear, actionable task title")
    time_estimate_minutes: Optional[int] = Field(
        None,
        description="Time estimate in minutes if mentioned"
    )
    due_date: Optional[str] = Field(
        None,
        description="Due date in YYYY-MM-DD format"
    )
    project_name: Optional[str] = Field(
        None,
        description="Project name if mentioned or inferred"
    )
    people_names: list[str] = Field(
        default_factory=list,
        description="Names of people mentioned"
    )
    priority: str = Field(
        default="medium",
        description="Priority: low, medium, high, or urgent"
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Relevant tags inferred from content"
    )
    context: Optional[str] = Field(
        None,
        description="Additional context or description"
    )


class TimeEstimate(BaseModel):
    """AI time estimation result"""

    estimate_minutes: int = Field(description="Estimated time in minutes")
    confidence: str = Field(description="Confidence level: low, medium, high")
    reasoning: str = Field(description="Brief explanation of estimate")
    suggestion: str = Field(description="Helpful message for user")
