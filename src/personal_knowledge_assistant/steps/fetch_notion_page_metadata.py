from zenml import step, get_step_context
from typing_extensions import Annotated
from loguru import logger

from src.personal_knowledge_assistant.models import DocumentMetadata
from src.personal_knowledge_assistant.notion.page_extractor import NotionPageFetcher

@step
def fetch_notion_page_metadata(
    database_id : str
) -> Annotated[list[DocumentMetadata], "notion_documents_metadata"]:
    """
    Fetches metadata of pages from a Notion database.

    Args:
        database_id (str): The ID of the Notion database.

    Returns:
        list[DocumentMetadata]: A list of DocumentMetadata objects containing metadata of the pages.
    """
    fetcher = NotionPageFetcher()

    notion_page_metadata = fetcher.fetch_pages_from_database(database_id=database_id)

    logger.info(f"Fetched {len(notion_page_metadata)} pages from Notion database {database_id}")
    
    get_step_context().add_output_metadata(
        output_name = "notion_documents_metadata",
        metadata = {
            "database_id": database_id,
            "number_of_documents": len(notion_page_metadata)
        }
    )

    return notion_page_metadata