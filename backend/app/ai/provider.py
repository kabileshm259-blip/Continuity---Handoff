from abc import ABC, abstractmethod
from app.models.ai_extraction import AIExtractionResult

class AIProvider(ABC):
    @abstractmethod
    async def extract_work_state(self, raw_notes: str) -> AIExtractionResult:
        """Extract structured work state from unstructured handoff notes.
        
        Note: The AI strictly extracts and explains facts.
        It does NOT decide operational status or policy logic.
        """
        pass
