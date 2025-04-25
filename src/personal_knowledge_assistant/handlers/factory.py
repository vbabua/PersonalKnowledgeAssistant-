
from src.personal_knowledge_assistant.domain.types import DataCategory
from src.personal_knowledge_assistant.handlers.base import CleaningHandler
from src.personal_knowledge_assistant.handlers.document_cleaner import (
    NotionDocumentCleaner,
    GenericDocumentCleaner,
)
class CleaningHandlerFactory:
    """
    Factory class for creating appropritate document cleaning handlers
    """
    @staticmethod
    def create_cleaning_handler(data_category : DataCategory) -> CleaningHandler:
        """
        Create a cleaning handler based on the data category.
        
        Args:
            data_category (DataCategory): The data category of the document.
            
        Returns:
            CleaningDispatcher: An instance of the appropriate cleaning handler.
        """
        if data_category == DataCategory.NOTION:
            return NotionDocumentCleaner()
        else:
            raise ValueError(f"Unsupported data category: {data_category}")