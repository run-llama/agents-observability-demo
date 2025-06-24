from pydantic import BaseModel, Field
from typing import List, Optional


class Syllabus(BaseModel):
    course_name: str = Field(description="Name of the course.")
    teaching_languages: List[str] = Field(
        description="Languages in which the course is taught. Assume the language to be the one in which the document is written, if teaching languages are not provided."
    )
    course_year: int = Field(
        description="Year in which the course is offered (use 1 for 1st year, 2 for 2nd year, etc.)",
        examples=[1, 2, 6, 3, 4, 5],
        ge=1,
        le=6,
    )
    keywords: List[str] = Field(
        description="Keywords to describe the course, if any.",
        default_factory=list,
    )
    summary: str = Field(
        description="Summary of the course.",
    )
    learning_objectives: List[str] = Field(
        description="List of learning objectives, if any.",
        default_factory=list,
    )
    evaluation_method: Optional[str] = Field(
        description="How is the evaluation of the course performed, if there is an evaluation. Leave empty if there is no evaluation.",
        default=None,
    )
