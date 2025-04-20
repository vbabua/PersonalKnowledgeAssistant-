from pydantic import BaseModel, Field
from pathlib import Path
import hashlib


class DocumentMetadata(BaseModel):
    id : str
    title : str
    properties : dict
    page_link : str

class Document(BaseModel):
    id : str
    metadata : DocumentMetadata
    content : str
    parent_metadata : DocumentMetadata | None = None
    child_urls: list[str] = Field(default_factory=list)

    def write(self, output_dir: Path, obfuscate: bool = False, also_save_as_txt: bool = False) -> None:
        """Write document to disk in JSON format and optionally as text.
        
        Args:
            output_dir: Directory to save files to
            obfuscate: If True, use a hash of the ID as filename
            also_save_as_txt: If True, also save content as plain text
        """
        # Create filename based on id or its hash
        filename = self.id
        if obfuscate:
            filename = hashlib.md5(self.id.encode()).hexdigest()
            
        # Save as JSON
        json_path = output_dir / f"{filename}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(self.model_dump_json(indent=2))
            
        # Optionally save content as plain text
        if also_save_as_txt:
            txt_path = output_dir / f"{filename}.txt"
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(self.content)