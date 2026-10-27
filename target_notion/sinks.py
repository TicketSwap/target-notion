"""notion target sink class, which handles writing streams."""

from __future__ import annotations

import os

from caseconverter import snakecase
from notion_client import Client
from notion_client.errors import HTTPResponseError
from retry import retry
from singer_sdk.sinks import BatchSink


class notionSink(BatchSink):  # noqa: N801
    """notion target sink class."""

    MAX_SIZE_DEFAULT = 100

    def __init__(self, **kwargs) -> None:  # noqa: ANN003
        """Initialize the sink."""
        super().__init__(**kwargs)
        self.client = Client(auth=self.config["api_key"])
        data_source_mapping = {
            mapping["extractor_namespace"]: {
                mapping["stream_name"]: mapping["data_source_id"]
            }
            for mapping in self.config["streams"]
        }
        self.data_source_id = data_source_mapping.get(
            os.environ.get("MELTANO_EXTRACTOR_NAMESPACE"), {}
        ).get(self.stream_name)
        if not self.data_source_id:
            msg = f"Data source ID not found for stream {self.stream_name}."
            raise ValueError(msg)
        self.data_source_schema = self.get_data_source_schema()
        self.key_property = self.key_properties[0]
        self.snake_key_property = snakecase(self.key_property)
        self.data_source_key_property = self.data_source_schema[
            self.snake_key_property
        ]["name"]

    def process_batch(self, context: dict) -> None:
        """Process a batch with the given batch context.

        This method must be overridden.

        If :meth:`~singer_sdk.BatchSink.process_record()` is not overridden,
        the `context["records"]` list will contain all records from the given batch
        context.

        If duplicates are merged, these can be tracked via
        :meth:`~singer_sdk.Sink.tally_duplicate_merged()`.

        Args:
            context: Stream partition or context dictionary.
        """
        records = [
            {snakecase(key): value for key, value in record.items()}
            for record in context["records"]
        ]
        existing_pages = self.get_existing_pages(records)
        filtered_records = [
            record
            for record in records
            if record[self.snake_key_property] not in existing_pages
        ]
        self.logger.info("Creating %d/%d pages.", len(filtered_records), len(records))
        for record in filtered_records:
            self.create_page(record)

    def get_existing_pages(self, records: list[dict]) -> list:
        """Get existing pages in the data_source."""
        _filter = {
            "or": [
                {
                    "property": self.data_source_key_property,
                    "title": {"equals": record[self.snake_key_property]},
                }
                for record in records
            ]
        }
        has_more = True
        start_cursor = None
        existing_pages = {}
        while has_more:
            pages = self.client.data_sources.query(
                data_source_id=self.data_source_id,
                start_cursor=start_cursor,
                filter_properties=[],
                filter=_filter,
            )
            existing_pages.update(
                {
                    page["properties"][self.data_source_key_property]["rich_text"][0][
                        "text"
                    ]["content"]: page["id"]
                    for page in pages["results"]
                }
            )
            has_more = pages["has_more"]
            start_cursor = pages.get("next_cursor")
        return existing_pages

    @retry(HTTPResponseError, tries=3, delay=1, backoff=4, max_delay=10)
    def create_page(self, record: dict) -> None:
        """Create the page.

        Args:
            record: Individual record in the stream.
            context: Stream partition or context dictionary.
        """
        self.client.pages.create(
            parent={"data_source_id": self.data_source_id},
            properties=self.create_page_properties(record),
        )

    def get_data_source_schema(self) -> dict:
        """Get the data_source schema.

        Returns:
            dict: The data_source schema.
        """
        data_source = self.client.data_sources.retrieve(self.data_source_id)
        return {
            snakecase(name): {"name": name, "type": _property["type"]}
            for name, _property in data_source["properties"].items()
        }

    def create_page_properties(self, record: dict) -> dict:
        """Create page properties from the record.

        Args:
            record: Individual record in the stream.

        Returns:
            dict: The page properties.
        """
        return {
            self.data_source_schema.get(key, {})["name"]: self.create_page_property(
                self.data_source_schema.get(key, {})["type"], value
            )
            for key, value in record.items()
            if key in self.data_source_schema and value
        }

    def create_page_property(self, _type: str, value) -> dict:  # noqa: ANN001, C901, PLR0912
        """Create a page property from the type and value."""
        match _type:
            case "title":
                _property = {
                    "id": "title",
                    "type": "title",
                    "title": [{"text": {"content": str(value)}}],
                }
            case "rich_text":
                _property = {"rich_text": [{"text": {"content": str(value)}}]}
            case "number":
                _property = {"number": float(value)}
            case "select":
                _property = {"select": {"name": str(value).replace(",", "")}}
            case "multi_select":
                _property = {
                    "multi_select": [
                        {"name": str(v).replace(",", "")} for v in value.split(", ")
                    ]
                }
            case "date":
                _property = {"date": {"start": value}}
            case "people":
                _property = {"people": [{"id": str(v)} for v in value.split(", ")]}
            case "files":
                _property = {
                    "files": [
                        {"name": v["name"], "url": v["url"]} for v in value.split(", ")
                    ]
                }
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
