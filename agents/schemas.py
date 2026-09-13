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

class CodeChange(BaseModel):
    file_path: str = Field(description="Relative path of the file being changed")
    new_content: str = Field(description="The complete new content of the file after the fix")
    explanation: str = Field(description="Brief explanation of what was changed and why")

class CoderOutput(BaseModel):
    changes: List[CodeChange] = Field(description="All file changes needed to fix the issue")

class ReviewVerdict(BaseModel):
    approved: bool = Field(description="True if the diff is acceptable to merge")
    reasoning: str = Field(description="Explanation for the verdict")
    concerns: List[str] = Field(
        default_factory=list,
        description="Specific issues found, empty if approved"
    )
