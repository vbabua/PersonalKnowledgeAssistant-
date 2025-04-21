

from src.personal_knowledge_assistant.domain.base.document import NotionDocument, DocumentMetadata
from src.personal_knowledge_assistant.utils.text_cleaning import clean_text, normalize_headings
from loguru import logger
from typing import List

class NotionDocumentCleaner:
    """Handler for cleaning Notion documents"""
    
    @staticmethod
    def clean(document: NotionDocument) -> NotionDocument:
        """
        Clean a Notion document by processing its content and metadata.
        
        Args:
            document: The original Document to clean
            
        Returns:
            Cleaned Document with the same structure
        """
        # Clean the text content
        cleaned_content = clean_text(document.content)
        cleaned_content = normalize_headings(cleaned_content)
        
        # Create a new document with cleaned content but preserving metadata
        cleaned_document = NotionDocument(
            id=document.id,
            metadata=document.metadata,
            content=cleaned_content,
            parent_metadata=document.parent_metadata,
            child_urls=document.child_urls
        )
        
        logger.info(f"Cleaned document {document.id}, original length: {len(document.content)}, " 
                    f"cleaned length: {len(cleaned_content)}")
        
        return cleaned_document
    
    @staticmethod
    def clean_batch(documents: List[NotionDocument]) -> List[NotionDocument]:
        """
        Clean a batch of Notion documents.
        
        Args:
            documents: List of Documents to clean
            
        Returns:
            List of cleaned Documents
        """
        cleaned_documents = []
        
        for document in documents:
            try:
                cleaned_document = NotionDocumentCleaner.clean(document)
                cleaned_documents.append(cleaned_document)
            except Exception as e:
                logger.error(f"Error cleaning document {document.id}: {str(e)}")
                # Either skip or add the original document
                cleaned_documents.append(document)
                
        logger.info(f"Cleaned {len(cleaned_documents)} documents")
        return cleaned_documents