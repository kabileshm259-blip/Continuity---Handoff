import os
from app.ai.provider import AIProvider
from app.ai.mock_provider import MockAIProvider
from app.ai.bedrock_provider import BedrockAIProvider

def get_ai_provider() -> AIProvider:
    """Factory to retrieve configured AI Provider based on environment.
    
    Defaults to MockAIProvider unless AI_PROVIDER=bedrock is explicitly configured.
    Uses standard AWS credential chain for BedrockAIProvider.
    """
    provider_type = os.getenv("AI_PROVIDER", "mock").strip().lower()
    
    if provider_type == "bedrock":
        return BedrockAIProvider()
    
    return MockAIProvider()
