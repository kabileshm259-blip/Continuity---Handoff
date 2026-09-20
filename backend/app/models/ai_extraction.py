from typing import List, Optional
from pydantic import BaseModel, Field

class ExtractedCommitment(BaseModel):
    case_hint: Optional[str] = Field(None, description="Hint or reference to related case/order")
    description: str = Field(..., description="What was committed/promised")
    committed_to: str = Field(..., description="Who the commitment was made to")
    expected_date: Optional[str] = Field(None, description="When the commitment is due")

class ExtractedBlocker(BaseModel):
    case_hint: Optional[str] = Field(None, description="Hint or reference to related case")
    description: str = Field(..., description="Description of the blocker")
    blocked_by: str = Field(..., description="Entity, person, or department blocking work")

class ExtractedDeadline(BaseModel):
    case_hint: Optional[str] = Field(None, description="Hint or reference to related case")
    description: str = Field(..., description="Description of the deadline")
    date_str: str = Field(..., description="Due date string e.g. 'Today', 'Tomorrow', 'Friday'")

class ExtractedException(BaseModel):
    case_hint: Optional[str] = Field(None, description="Hint or reference to related case/order")
    expected: str = Field(..., description="What was expected to occur or match")
    found: str = Field(..., description="What was actually found")
    evidence: str = Field(..., description="Evidence, system records, or notes showing discrepancy")
    impact: Optional[str] = Field(None, description="Business impact")
    required_action: str = Field(..., description="Action required to investigate/resolve exception")

class ExtractedNextAction(BaseModel):
    case_hint: Optional[str] = Field(None, description="Hint or reference to related case")
    action: str = Field(..., description="Specific next actionable step")
    assignee: Optional[str] = Field(None, description="Suggested person or role")

class ExtractedWorkItem(BaseModel):
    case_hint: Optional[str] = Field(None, description="Hint or reference to related case")
    title: str = Field(..., description="Title of work item")
    description: Optional[str] = Field(None, description="Details of the work item")

class AIExtractionResult(BaseModel):
    completed: List[ExtractedWorkItem] = Field(default_factory=list)
    unresolved: List[ExtractedWorkItem] = Field(default_factory=list)
    commitments: List[ExtractedCommitment] = Field(default_factory=list)
    blockers: List[ExtractedBlocker] = Field(default_factory=list)
    deadlines: List[ExtractedDeadline] = Field(default_factory=list)
    exceptions: List[ExtractedException] = Field(default_factory=list)
    next_actions: List[ExtractedNextAction] = Field(default_factory=list)
