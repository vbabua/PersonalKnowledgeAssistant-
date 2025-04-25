# src/personal_knowledge_assistant/handlers/dispatcher.py
from loguru import logger

from src.personal_knowledge_assistant.domain import Document
from src.personal_knowledge_assistant.domain.documents.notion import NotionDocument
from src.personal_knowledge_assistant.domain.types import DataCategory
from src.personal_knowledge_assistant.handlers.factory import CleaningHandlerFactory

class CleaningDispatcher:
    """Dispatches documents to the appropriate cleaning handler based on document type."""
    
    @classmethod
    def dispatch(cls, document: Document) -> Document:
        """Route document to the appropriate cleaner based on its category.
        
        Args:
            document: The document to clean
            
        Returns:
            The cleaned document
        """
        try:
            # Extract the data category from the document
            data_category = cls._get_document_category(document)
            
            # Get appropriate handler from factory
            handler = CleaningHandlerFactory.create_handler(data_category)
            
            # Clean the document
            clean_document = handler.clean(document)

            logger.info("Document cleaned successfully.", data_category=data_category, cleaned_content_len=len(clean_document.content))
        
            return clean_document
        except Exception as e:
            logger.error(f"Error cleaning document {document.id}: {str(e)}")
            # Return original document if cleaning fails
            return document
    
    @staticmethod
    def _get_document_category(document: Document) -> DataCategory:
        """Extract the category from a document.
        
        Args:
            document: The document to extract category from
            
        Returns:
            The document's category
            
        Raises:
            ValueError: If the category cannot be determined
        """
        if hasattr(document, "Config") and hasattr(document.Config, "category"):
            return document.Config.category
            
        raise ValueError(f"Could not determine category for document: {type(document).__name__}")