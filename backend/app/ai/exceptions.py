"""Application-level exceptions for Amazon Bedrock AI extraction."""

class BedrockError(Exception):
    """Base exception for Bedrock AI operations."""
    pass

class BedrockConfigurationError(BedrockError):
    """Raised when Bedrock configuration is missing or invalid (e.g. BEDROCK_MODEL_ID not set)."""
    pass

class BedrockInferenceError(BedrockError):
    """Raised when Bedrock client or API invocation fails (e.g. credentials, model access, rate limit)."""
    pass

class BedrockExtractionError(BedrockError):
    """Raised when Bedrock returns malformed JSON or fails Pydantic schema validation."""
    pass
