from zenml import pipeline
from pathlib import Path
from loguru import logger

from src.personal_knowledge_assistant.steps.fetch_notion_page_metadata import fetch_notion_page_metadata
from src.personal_knowledge_assistant.steps.extract_notion_page_content import extract_notion_page_content
from src.personal_knowledge_assistant.steps.save_documents_to_disk import save_documents_to_disk
from src.personal_knowledge_assistant.steps.clean_notion_documents import clean_notion_documents

@pipeline
def notion_to_vector_pipeline(database_ids : list[str], 
                              data_directory : Path
                              ) -> None:
    """
    A pipeline that extracts data from Notion and converts it into vector embeddings.
    Args:
        database_ids (list[str]) : List of Notion database IDs to extract data from.
        data_directory (Path) : Directory to store the extracted data.
    """
    notion_data_directory = data_directory/"notion_data"
    notion_data_directory.mkdir(parents=True, exist_ok=True)
    
    # Extract data from Notion  
    for index, database_id in enumerate(database_ids):
        logger.info(f"Extracting data from Notion database {database_id}...")

        # Fetch metadata from Notion
        notion_page_metadata = fetch_notion_page_metadata(database_id=database_id)

        # Extract content from Notion pages
        documents = extract_notion_page_content(notion_documents_metadata=notion_page_metadata)

        # Clean the documents
        cleaned_documents = clean_notion_documents(documents = documents)
       
        resutlting_documents = save_documents_to_disk(documents = cleaned_documents, output_dir = notion_data_directory / f"notion_data_{index}")

        logger.info(f"Completed extraction and saving for Notion database {database_id}.")

