"""notion target sink class, which handles writing streams."""

from __future__ import annotations

from caseconverter import snakecase
from notion_client import Client
from notion_client.errors import HTTPResponseError
from retry import retry
from singer_sdk.sinks import RecordSink


class notionSink(RecordSink):
    """notion target sink class."""

    def __init__(self, **kwargs) -> None:  # noqa: ANN003
        """Initialize the sink."""
        super().__init__(**kwargs)
        self.client = Client(auth=self.config["api_key"])
        self.database_schema = self.get_database_schema()

    @retry(HTTPResponseError, tries=3, delay=1, backoff=4, max_delay=10)
    def process_record(self, record: dict, context: dict) -> None:
        """Process the record.

        Args:
            record: Individual record in the stream.
            context: Stream partition or context dictionary.
        """
        snakecase_record = {snakecase(key): value for key, value in record.items()}
        self.client.pages.create(
            parent={"database_id": self.config["database_id"]},
            properties=self.create_page_properties(snakecase_record),
        )

    def get_database_schema(self) -> dict:
        """Get the database schema.

        Returns:
            dict: The database schema.
        """
        db = self.client.databases.retrieve(self.config["database_id"])
        return {
            snakecase(name): {"name": name, "type": _property["type"]} for name, _property in db["properties"].items()
        }

    def create_page_properties(self, record: dict) -> dict:
        """Create page properties from the record.

        Args:
            record: Individual record in the stream.

        Returns:
            dict: The page properties.
        """
        return {
            self.database_schema.get(key, {})["name"]: self.create_page_property(
                self.database_schema.get(key, {})["type"], value
            )
            for key, value in record.items()
            if key in self.database_schema and value
        }

    def create_page_property(self, _type: str, value) -> dict:
        """Create a page property from the type and value."""
        match _type:
            case "title":
                _property = {"id": "title", "type": "title", "title": [{"text": {"content": str(value)}}]}
            case "rich_text":
                _property = {"rich_text": [{"text": {"content": str(value)}}]}
            case "number":
                _property = {"number": float(value)}
            case "select":
                _property = {"select": {"name": str(value).replace(",", "")}}
            case "multi_select":
                _property = {"multi_select": [{"name": str(v).replace(",", "")} for v in value.split(", ")]}
            case "date":
                _property = {"date": {"start": value}}
            case "people":
                _property = {"people": [{"id": str(v)} for v in value.split(", ")]}
            case "files":
                _property = {"files": [{"name": v["name"], "url": v["url"]} for v in value.split(", ")]}
            case "checkbox":
                _property = {"checkbox": value}
            case "url":
                _property = {"url": str(value)}
            case "email":
                _property = {"email": str(value)}
            case "phone_number":
                _property = {"phone_number": str(value)}
            case "relation":
                _property = {"relation": [{"id": v} for v in value.split(", ")]}
            case _:
                msg = f"Unsupported property type: {_type}"
                raise ValueError(msg)
        return _property
