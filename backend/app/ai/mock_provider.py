import re
from app.ai.provider import AIProvider
from app.models.ai_extraction import (
    AIExtractionResult, ExtractedCommitment, ExtractedBlocker,
    ExtractedDeadline, ExtractedException, ExtractedNextAction,
    ExtractedWorkItem
)

class MockAIProvider(AIProvider):
    """Mock AI Provider for Phase 1 local development and hackathon testing.
    
    Produces structured facts from unstructured text without requiring AWS Bedrock credentials.
    """

    async def extract_work_state(self, raw_notes: str) -> AIExtractionResult:
        notes_lower = raw_notes.lower()
        
        # Check if this matches or contains elements of the primary hackathon demo prompt
        is_primary_demo = (
            "replacement request" in notes_lower or 
            "invoice correction" in notes_lower or 
            "8821" in notes_lower
        )
        
        if is_primary_demo:
            return self._build_canonical_demo_extraction()
        
        # Dynamic fallback for arbitrary custom user inputs during demo
        return self._heuristic_extraction(raw_notes)

    def _build_canonical_demo_extraction(self) -> AIExtractionResult:
        return AIExtractionResult(
            completed=[
                ExtractedWorkItem(
                    case_hint="CASE-1042",
                    title="Customer damaged product photos received",
                    description="Customer sent damaged product photos yesterday; initial damage assessment completed."
                ),
                ExtractedWorkItem(
                    case_hint="CASE-1042",
                    title="Warehouse initial contact",
                    description="Contacted warehouse team regarding replacement stock availability."
                ),
                ExtractedWorkItem(
                    case_hint="CASE-1038",
                    title="Updated invoice submitted to Finance",
                    description="Prepared and emailed updated invoice correction to Finance this morning."
                )
            ],
            unresolved=[
                ExtractedWorkItem(
                    case_hint="CASE-1042",
                    title="Warehouse stock confirmation",
                    description="Warehouse has not yet confirmed stock availability for replacement."
                ),
                ExtractedWorkItem(
                    case_hint="CASE-1038",
                    title="Finance approval pending",
                    description="Finance has not yet approved the corrected invoice adjustment."
                ),
                ExtractedWorkItem(
                    case_hint="CASE-8821",
                    title="Order #8821 item discrepancy investigation",
                    description="Resolve conflict between warehouse SKU records and delivered physical item."
                )
            ],
            commitments=[
                ExtractedCommitment(
                    case_hint="CASE-1042",
                    description="Update customer on replacement shipment status",
                    committed_to="Priya (Customer)",
                    expected_date="Friday"
                )
            ],
            blockers=[
                ExtractedBlocker(
                    case_hint="CASE-1042",
                    description="Warehouse stock confirmation pending",
                    blocked_by="Warehouse Team"
                ),
                ExtractedBlocker(
                    case_hint="CASE-1038",
                    description="Finance department approval required before invoice can be re-issued",
                    blocked_by="Finance Department"
                )
            ],
            deadlines=[
                ExtractedDeadline(
                    case_hint="CASE-1042",
                    description="Warehouse stock confirmation expected",
                    date_str="Tomorrow"
                ),
                ExtractedDeadline(
                    case_hint="CASE-1042",
                    description="Customer update promise",
                    date_str="Friday"
                ),
                ExtractedDeadline(
                    case_hint="CASE-1038",
                    description="Finance response expected",
                    date_str="Today"
                )
            ],
            exceptions=[
                ExtractedException(
                    case_hint="CASE-8821",
                    expected="Warehouse record and customer delivery should match",
                    found="Customer reports receiving a completely different item than ordered",
                    evidence="Warehouse system shows correct SKU dispatched, but customer delivered package contains different physical item",
                    impact="Inventory mismatch and customer delivery failure",
                    required_action="Verify shipment evidence and inspect physical packing bay records"
                )
            ],
            next_actions=[
                ExtractedNextAction(
                    case_hint="CASE-1042",
                    action="Follow up with warehouse tomorrow morning for stock confirmation",
                    assignee="Priya Sharma"
                ),
                ExtractedNextAction(
                    case_hint="CASE-1038",
                    action="Follow up with Finance today if no response by 3 PM",
                    assignee="Priya Sharma"
                ),
                ExtractedNextAction(
                    case_hint="CASE-8821",
                    action="Verify shipment evidence and contact packing supervisor",
                    assignee="Priya Sharma"
                )
            ]
        )

    def _heuristic_extraction(self, text: str) -> AIExtractionResult:
        """Heuristic parser for arbitrary custom notes pasted during testing."""
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        result = AIExtractionResult()

        for line in lines:
            line_lower = line.lower()

            if any(w in line_lower for w in ["done", "completed", "handled", "sent", "finished", "resolved"]):
                result.completed.append(ExtractedWorkItem(title=line, description=line))
            elif any(w in line_lower for w in ["promise", "promised", "commit", "committed", "guarantee"]):
                result.commitments.append(
                    ExtractedCommitment(
                        description=line,
                        committed_to="Stakeholder / Customer",
                        expected_date="As agreed"
                    )
                )
            elif any(w in line_lower for w in ["blocked", "waiting", "waiting for", "pending approval", "hasn't approved"]):
                result.blockers.append(
                    ExtractedBlocker(
                        description=line,
                        blocked_by="External dependency"
                    )
                )
            elif any(w in line_lower for w in ["conflict", "mismatch", "wrong", "discrepancy", "exception"]):
                result.exceptions.append(
                    ExtractedException(
                        expected="System records and reported outcome should match",
                        found=line,
                        evidence="Discrepancy reported in handoff notes",
                        required_action="Investigate conflicting records and reconcile"
                    )
                )
            elif any(w in line_lower for w in ["deadline", "today", "tomorrow", "friday", "monday", "by "]):
                result.deadlines.append(
                    ExtractedDeadline(
                        description=line,
                        date_str="Upcoming"
                    )
                )
            else:
                result.unresolved.append(ExtractedWorkItem(title=line, description=line))

            if any(w in line_lower for w in ["follow up", "next", "should", "need to", "must"]):
                result.next_actions.append(
                    ExtractedNextAction(
                        action=line,
                        assignee="Assigned Employee"
                    )
                )

        if not result.unresolved and lines:
            result.unresolved.append(ExtractedWorkItem(title="General handoff review", description=lines[0]))

        return result
