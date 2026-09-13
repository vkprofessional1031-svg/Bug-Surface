from pydantic import BaseModel, Field
from typing import List

class Plan(BaseModel):
    root_cause_hypothesis: str = Field(
        description="A short guess at what's actually causing the bug"
    )
    files_to_touch: List[str] = Field(
        description="Relative file paths likely needing changes"
    )
    subtasks: List[str] = Field(
        description="Ordered, concrete steps to fix the issue"
    )
