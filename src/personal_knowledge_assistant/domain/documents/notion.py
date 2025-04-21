from pydantic import Field
from typing import Optional, List

from ..base.document import Document, DocumentMetadata
from ..types import DataCategory

class NotionDocumentMetadata(DocumentMetadata):
    has_images: bool = False
    
class NotionDocument(Document):
    metadata: NotionDocumentMetadata
    
    class Config:
        name = "notion_document"
        category = DataCategory.NOTION