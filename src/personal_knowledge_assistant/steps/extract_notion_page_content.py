from zenml import step, get_step_context
from typing_extensions import Annotated

from src.personal_knowledge_assistant.models import DocumentMetadata, Document
from src.personal_knowledge_assistant.notion.content_extractor import NotionContentExtractor
from loguru import logger

@step
def extract_notion_page_content(
    notion_documents_metadata: Annotated[list[DocumentMetadata], "notion_documents_metadata"]
) -> Annotated[list[Document], "notion_documents"]:
    """
    Extracts content from Notion pages using their metadata.

    Args:
        notion_documents_metadata (list[DocumentMetadata]): A list of DocumentMetadata objects containing metadata of the pages.

    Returns:
        list[Document]: A list of Document objects containing the extracted content.
    """
    extractor = NotionContentExtractor()

    # Extract content for each page
    notion_documents = [extractor.extract_content(metadata) for metadata in notion_documents_metadata]

    logger.info(f"Extracted content from {len(notion_documents)} Notion pages.")

    get_step_context().add_output_metadata(
        output_name = "notion_documents",
        metadata = {
            "number_of_documents": len(notion_documents)
        }
    )

    return notion_documents
