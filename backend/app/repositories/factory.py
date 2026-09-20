import os
from typing import Optional
from app.repositories.base import BaseRepository
from app.repositories.memory_repository import InMemoryRepository
from app.repositories.dynamodb_repository import DynamoDBRepository

_repo_instance: Optional[BaseRepository] = None

def get_repository() -> BaseRepository:
    """Factory to retrieve configured repository based on REPOSITORY_PROVIDER environment variable.
    
    Options:
    - 'memory' (default): In-memory thread-safe repository with demo seed data.
    - 'dynamodb': Real Amazon DynamoDB repository using standard AWS credential chain.
    """
    global _repo_instance
    if _repo_instance is not None:
        return _repo_instance

    provider = os.getenv("REPOSITORY_PROVIDER", "memory").strip().lower()
    
    if provider == "dynamodb":
        _repo_instance = DynamoDBRepository()
    else:
        _repo_instance = InMemoryRepository()

    return _repo_instance

def reset_repository_instance():
    """Reset repository singleton (useful for testing)."""
    global _repo_instance
    _repo_instance = None
