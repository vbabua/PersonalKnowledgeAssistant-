from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from src.personal_knowledge_assistant.domain import Document

T = TypeVar('T', bound=Document)

class CleaningHandler(ABC, Generic[T]):
    """Base abstract class for all document cleaning handlers."""
    
    @abstractmethod
    def clean(self, document: T) -> T:
        """
        Clean the document and return the cleaned version.
        
        Args:
            document: The document to clean
            
        Returns:
            The cleaned document
        """
        pass