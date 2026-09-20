"""Storage module re-exporting from app.repositories for backward compatibility."""
from app.repositories.base import BaseRepository
from app.repositories.memory_repository import InMemoryRepository
from app.repositories.dynamodb_repository import DynamoDBRepository
from app.repositories.factory import get_repository, reset_repository_instance

__all__ = [
    "BaseRepository",
    "InMemoryRepository",
    "DynamoDBRepository",
    "get_repository",
    "reset_repository_instance",
]
