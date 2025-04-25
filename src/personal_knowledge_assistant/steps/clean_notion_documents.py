from typing import List, Annotated
from zenml import step, get_step_context
from src.personal_knowledge_assistant.domain.types import Document
from personal_knowledge_assistant.handlers.factory import NotionDocumentCleaner
from loguru import logger

@step
def clean_notion_documents(
    documents: Annotated[list[Document], "extracted_notion_documents"]
) -> Annotated[list[Document], "cleaned_notion_documents"]:
    """
    Clean extracted Notion documents.
    
    Args:
        documents: List of raw documents extracted from Notion.
        
    Returns:
        List of cleaned documents.
    """
    logger.info(f"Cleaning {len(documents)} Notion documents")
    
    cleaned_documents = []

    for document in documents:
        cleaned_document = CleaningDispatcher.dispatch(document)
        cleaned_documents.append(cleaned_document)

    # Add metadata about the cleaning process to the step output
    step_context = get_step_context()
    step_context.add_output_metadata(
        output_name="cleaned_documents",
        metadata={
            "num_documents": len(cleaned_documents),
            "cleaning_source": "notion",
        }
    )
    
    logger.info(f"Successfully cleaned {len(cleaned_documents)} documents")
    return cleaned_documents
    