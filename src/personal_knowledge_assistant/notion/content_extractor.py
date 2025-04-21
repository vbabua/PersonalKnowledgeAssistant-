from src.personal_knowledge_assistant import settings
from src.personal_knowledge_assistant.domain.documents.notion import NotionDocumentMetadata, NotionDocument

import requests
from loguru import logger

class NotionContentExtractor:
    """
    A class to extract content from Notion pages.
    """

    def __init__(self, notion_api_key: str = settings.NOTION_API_KEY):
        """
        Initialize the NotionContentExtractor with the Notion API key.

        Args:
            notion_api_key (str): The Notion API key for authentication.
        """
        if notion_api_key is None:
            raise ValueError("Notion API key is required.")
        
        self.api_key = notion_api_key
    
    def extract_content(self, metadata : NotionDocumentMetadata) -> NotionDocument:
        """
        Extract content from a Notion page using its metadata.

        Args:
            metadata (NotionDocumentMetadata): Metadata of the Notion page.

        Returns:
            NotionDocument: The extracted content as a NotionDocument object.
        """
        blocks = self._retrieve_page_elements(metadata.id)
        content, page_link = self._process_elements(blocks)

        # Extract parent metadata if present and convert to NotionDocumentMetadata object
        parent_metadata = metadata.properties.pop("Parent", None)
        if parent_metadata:
            parent_metadata = NotionDocumentMetadata(**parent_metadata)
        
        return NotionDocument(
            id=metadata.id,
            metadata=metadata,
            parent_metadata=parent_metadata,
            content=content,
            page_link = page_link
        )
    
    def _retrieve_page_elements(self, 
                                page_id: str
                                )-> list[dict]:
        """
        Retrieve the blocks of a Notion page.

        Args:
            page_id (str): The ID of the Notion page.

        Returns:
            list[dict]: A list of blocks from the Notion page.
        """

        endpoint = f"https://api.notion.com/v1/blocks/{page_id}/children"

        request_headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Notion-Version": "2022-06-28"
        }
        all_blocks = []
        has_more = True
        next_cursor = None

        try:
            while has_more:
                params = {"page_size" : 100}
                if next_cursor:
                    params["start_cursor"] = next_cursor
                
                response = requests.get(endpoint, headers = request_headers, params = params, timeout = 10)
                response.raise_for_status()

                data = response.json()
                all_blocks.extend(data.get("results", []))

                has_more = data.get("has_more", False)

                next_cursor = data.get("next_cursor")

            return all_blocks
        except requests.exceptions.RequestException as e:
            error_details = f"Faled to retireve Notion page content : {e}"

            if hasattr(e, "response") and e.response is not None:
                error_details += f"(Status : {e.response.status_code}, Response : {e.response.text})"

            logger.exception(error_details)
            
            return []
        except Exception:
            logger.exception("Error retrieving Notion page content")
            return []
        
    def _process_elements(
        self,
        elements: list[dict],
        depth: int = 0
    ) -> tuple[str, list[str]]:
        """
        Process Notion blocks into text content and extract child URLs.

        Args:
            elements : List of Notion content elements.
            depth : Current nesting level for recursive processing.

        Returns:
            tuple[str, list[str]] : Tuple containing processed text and list of child URLs
        """
        content = ""
        child_urls = []

        for element in elements:
            element_type = element.get("type")
            element_id = element.get("id")

            # Headings
            if element_type in {"heading_1", "heading_2", "heading_3"}:
                content += f"# {self._extract_text(element[element_type].get('rich_text', []))}\n\n"
                child_urls.extend(self._gather_links(element[element_type].get("rich_text", [])))

            # Paragraphs and Quotes
            elif element_type in {"paragraph", "quote"}:
                content += f"{self._extract_text(element[element_type].get('rich_text', []))}\n"
                child_urls.extend(self._gather_links(element[element_type].get("rich_text", [])))

            # List Items
            elif element_type in {"bulleted_list_item", "numbered_list_item", "toggle"}:
                marker = "-" if element_type != "numbered_list_item" else "1."
                text = self._extract_text(element[element_type].get("rich_text", []))
                content += f"{marker} {text}\n"
                child_urls += self._gather_links(element[element_type].get("rich_text", []))
                if element_type == "toggle" and element.get("has_children"):
                    nested = self._retrieve_page_elements(element_id)
                    nt, nr = self._process_elements(nested, depth + 1)
                    indent = "\n".join("    " + ln for ln in nt.split("\n"))
                    content += f"\n{indent}\n"
                    child_urls += nr
            
            # To-do Items
            elif element_type == "to_do":
                content += f"[] {self._extract_text(element['to_do'].get('rich_text', []))}\n"
                child_urls.extend(self._gather_links(element[element_type].get("rich_text", [])))

            # Pdfs
            elif element_type == "pdf":
                pdf = element["pdf"]
                url = pdf.get("external", {}).get("url") or pdf.get("file", {}).get("url")
                content += f"[PDF]({url})\n"
                child_urls.append(url)
            
            # Code Blocks
            elif element_type == "code":
                content += f"```\n{self._extract_text(element['code'].get('rich_text', []))}\n```\n"
                child_urls.extend(self._gather_links(element[element_type].get("rich_text", [])))

            # Embeds
            elif element_type == "embed":
                url = element["embed"].get("url", "")
                content += f"[Embed]({url})\n"
                child_urls.append(url)

            # Image Blocks
            elif element_type == "image":
                image_url = (
                    element["image"].get("external", {}).get("url") or
                    element["image"].get("file", {}).get("url", "No URL")
                )
                caption_elements = element["image"].get("caption", [])
                caption = self._extract_text(caption_elements)
                content += f"![{caption or 'Image'}]({image_url})\n"

            # Link Preview
            elif element_type == "link_preview":
                url = element.get("link_preview", {}).get("url", "")
                content += f"[Link]({url})\n"
                child_urls.append(self._standardize_url(url))
            
            # Table rows
            elif element_type == "table_row":
                cells = element["table_row"].get("cells", [])
                cell_texts = [ self._extract_text(cell) for cell in cells ]
                content += "| " + " | ".join(cell_texts) + " |\n"
            
            # Table blocks
            elif element_type == "table":
                rows = element["table"].get("rows", [])
                if rows:
                    headers = [self._extract_text(cell.get("rich_text", [])) for cell in rows[0]]
                    content += "| " + " | ".join(headers) + " |\n"
                    content += "| " + " | ".join("---" for _ in headers) + " |\n"
                    for row in rows[1:]:
                        cells = [self._extract_text(c.get("rich_text", [])) for c in row]
                        content += "| " + " | ".join(cells) + " |\n"
                content += "\n"

            # Column lists: just unwrap into their child columns
            elif element_type == "column_list":
                # fetch all the child columns and process them inline at the same depth
               if element.get("has_children"):
                    cols = self._retrieve_page_elements(element_id)
                    col_text, col_urls = self._process_elements(cols, depth)
                    content += col_text + "\n"
                    child_urls.extend(col_urls)

            # Individual column: unwrap its children too
            elif element_type == "column":
                if element.get("has_children"):
                    cols = self._retrieve_page_elements(element_id)
                    col_text, col_urls = self._process_elements(cols, depth)
                    content += col_text + "\n"
                    child_urls.extend(col_urls)
            elif element_type == "child_database":
                title = element["child_database"].get("title", "")
                content += f"**Database:** {title}\n"

            # Dividers
            elif element_type == "divider":
                content += "---\n\n"

            # Child Pages (only up to a certain depth)
            elif element_type == "child_page" and depth < 3:
                child_id = element["id"]
                child_title = element.get("child_page", {}).get("title", "Untitled")
                content += f"\n\n<subpage>\n# {child_title}\n\n"

                if 'id' in element:
                    child_page_url = f"https://www.notion.so/{element['id'].replace('-', '')}"
                    child_urls.append(child_page_url)

                child_elements = self._retrieve_page_elements(child_id)
                child_text, child_refs = self._process_elements(child_elements, depth + 1)
                content += child_text + "\n</subpage>\n\n"
                child_urls.extend(child_refs)
            
            # Synced blocks: recursively pull in their children
            elif element_type == "synced_block":
                # optional placeholder or header
                content += "[Synced block start]\n"
                if element.get("has_children"):
                    nested = self._retrieve_page_elements(element_id)
                    nested_text, nested_urls = self._process_elements(nested, depth + 1)
                    content += nested_text + "\n[Synced block end]\n\n"
                    child_urls.extend(nested_urls)

            # Callouts: render as blockquote, preserving emoji/icon if present
            elif element_type == "callout":
                # grab emoji or icon if any
                icon = element["callout"].get("icon", {})
                prefix = ""
                if icon.get("type") == "emoji":
                    prefix = icon.get("emoji") + " "
                text = self._extract_text(element["callout"].get("rich_text", []))
                content += f"> {prefix}{text}\n\n"

            # Unsupported or unknown block types
            else:
                logger.debug(f"Skipping unsupported element type: {element_type}")

            # Nested Content
            if (
                element_type != "child_page"
                and "has_children" in element
                and element["has_children"]
            ):
                nested_elements = self._retrieve_page_elements(element_id)
                nested_text, nested_refs = self._process_elements(nested_elements, depth + 1)
                content += (
                    "\n".join("\t" + line for line in nested_text.split("\n"))
                    + "\n\n"
                )
                child_urls.extend(nested_refs)

        seen = set()
        unique_child_urls = [x for x in child_urls if not (x in seen or seen.add(x))]
        return content.strip(), unique_child_urls
    
    def _extract_text(self, text_elements: list[dict]) -> str:
        """Extract readable text from Notion rich text elements.

        Args:
            text_elements: List of Notion rich text elements.

        Returns:
            Formatted text content.
        """
        content = ""
        for element in text_elements:
            if element.get("href"):
                content += f"[{element.get('plain_text', '')}]({element.get('href', '')})"
            else:
                content += element.get("plain_text", "")
        return content

    def _gather_links(self, text_elements: list[dict]) -> list[str]:
        """Collect links from Notion rich text elements.

        Args:
            text_elements: List of Notion rich text elements.

        Returns:
            List of standardized URLs.
        """
        links = []
        for element in text_elements:
            link = None
            if element.get("href"):
                link = element["href"]
            elif "url" in element.get("annotations", {}):
                link = element["annotations"]["url"]

            if link:
                links.append(self._standardize_url(link))

        return links

    def _standardize_url(self, url: str) -> str:
        """Ensure URL follows a consistent format.

        Args:
            url: URL to standardize.

        Returns:
            Standardized URL.
        """
        if not url.endswith("/"):
            url += "/"
        return url