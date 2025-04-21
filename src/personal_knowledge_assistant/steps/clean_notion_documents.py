from typing import List, Annotated
from zenml import step, get_step_context
from src.personal_knowledge_assistant.domain.types import Document
from src.personal_knowledge_assistant.handlers.document_cleaner import NotionDocumentCleaner
from loguru import logger

@step
def clean_notion_documents(
    documents: Annotated[List[Document], "notion_documents"]
) -> Annotated[List[Document], "cleaned_documents"]:
    """
    ZenML step to clean Notion documents.
    
    Args:
        documents: List of raw Notion documents
        
    Returns:
        List of cleaned Notion documents
    """
    logger.info(f"Cleaning {len(documents)} Notion documents")
    
    # Clean the documents
    cleaned_documents = NotionDocumentCleaner.clean_batch(documents)
    
    # Add metadata for tracking
    step_context = get_step_context()
    metadata = {
        "num_documents": len(documents),
        "num_cleaned_documents": len(cleaned_documents),
        "avg_original_length": sum(len(doc.content) for doc in documents) / max(len(documents), 1),
        "avg_cleaned_length": sum(len(doc.content) for doc in cleaned_documents) / max(len(cleaned_documents), 1),
    }
    step_context.add_output_metadata(output_name="cleaned_documents", metadata=metadata)
    
    return cleaned_documents