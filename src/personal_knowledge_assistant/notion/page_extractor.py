from src.personal_knowledge_assistant import settings
from src.personal_knowledge_assistant.domain.documents.notion import NotionDocumentMetadata

import json
import requests
from loguru import logger
from typing import Dict, Any
from datetime import datetime, timezone
from pathlib import Path


class NotionPageFetcher:
    def __init__(self, 
                 api_key: str | None = settings.NOTION_API_KEY,
                 timestamp_file: Path | None = None
    ) -> None:
        if api_key is None:
            raise ValueError("Notion API key is required.")
        
        self.api_key = api_key
        self.timestamp_file = timestamp_file or Path("last_run.txt")

    def fetch_pages_from_database(
        self,
        database_id: str,
        filter_params: str | None = None,
        since: str | None = None
    ) -> list[NotionDocumentMetadata]:
        
        # Use stored timestamp from file if not provided explicilty
        if since is None and self.timestamp_file.exists():
            since = self.timestamp_file.read_text().strip()

        endpoint = f"https://api.notion.com/v1/databases/{database_id}/query"
        request_headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }

        filter_body: Dict[str, Any] = {}
        if filter_params and filter_params.strip():
            try:
                filter_body = json.loads(filter_params)
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON format for filter parameters.")
                return []

        # Add timestamp filter to return only updated pages
        if since:
            try:
                # Validate the timestamp format
                datetime.fromisoformat(since.replace("Z", "+00:00"))
                time_filter = {
                    "timestamp": "last_edited_time",
                    "last_edited_time": {
                        "after": since
                    }
                }

                # Combine with existing filter (if any)
                if "filter" in filter_body:
                    filter_body["filter"] = {
                        "and": [
                            filter_body["filter"],
                            time_filter
                        ]
                    }
                else:
                    filter_body["filter"] = time_filter
            except Exception as e:
                logger.opt(exception=True).debug(f"Invalid 'since' value: {since} → {e}")
                return []

        try:
            response = requests.post(
                endpoint,
                headers=request_headers,
                json=filter_body
            )
            
            response.raise_for_status()
            pages = response.json().get("results", [])
        except requests.exceptions.RequestException as e:
            logger.exception(
                f"Error querying Notion database. Status code: {getattr(e.response, 'status_code', 'N/A')}, "
                f"Response: {getattr(e.response, 'text', 'No response body')}"
            )
            return []
        except Exception as e:
            logger.exception(f"An unexpected error occurred: {e}")
            return []

        # Update timestamp file to track last run time
        now = datetime.now(timezone.utc).isoformat()
        try:
            self.timestamp_file.write_text(now)
        except Exception:
            pass  # silently fail to avoid blocking logic

        return [self._transform_page_metadata(p) for p in pages]

    def _transform_page_metadata(
        self,
        page: dict[str, Any]
    ) -> NotionDocumentMetadata:
        properties = self._extract_properties(page.get("properties", {}))

        # Use name as document title
        title = properties.pop("Name")

        # Add parent metadata if the page belongs to a database
        if page.get("parent"):
            properties["parent"] = {
                "id": page["parent"].get("database_id", ""),
                "title": "",
                "properties": {},
                "page_link": ""
            }

        return NotionDocumentMetadata(
            id=page["id"],
            title=title,
            properties=properties,
            page_link=page.get("url", "")
        )

    def _extract_properties(
        self,
        properties: dict
    ) -> dict:
        extracted_properties = {}

        for key, value in properties.items():
            property_type = value.get("type")

            if property_type == "select":
                extracted_properties[key] = value.get("select", {}).get("name")
            elif property_type == "multi_select":
                extracted_properties[key] = [
                    item.get("name") for item in value.get("multi_select", [])
                ]
            elif property_type == "title":
                extracted_properties[key] = "\n".join(
                    item.get("plain_text", "") for item in value.get("title", [])
                )
            elif property_type == "rich_text":
                extracted_properties[key] = " ".join(
                    item.get("plain_text", "") for item in value.get("rich_text", [])
                )
            elif property_type == "number":
                extracted_properties[key] = value.get("number")
            elif property_type == "checkbox":
                extracted_properties[key] = value.get("checkbox")
            elif property_type == "date":
                date_value = value.get("date", {})
                if date_value:
                    extracted_properties[key] = {
                        "start": date_value.get("start"),
                        "end": date_value.get("end"),
                    }
            elif property_type == "database_id":
                extracted_properties[key] = value.get("database_id")
            else:
                # For any unrecongnized propertu type, store the raw value
                extracted_properties[key] = value

        return extracted_properties