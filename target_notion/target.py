"""notion target class."""

from __future__ import annotations

from singer_sdk import typing as th
from singer_sdk.target_base import Target

from target_notion.sinks import (
    notionSink,
)


class Targetnotion(Target):
    """Sample target for notion."""

    name = "target-notion"

    config_jsonschema = th.PropertiesList(
        th.Property(
            "streams",
            th.ArrayType(
                th.ObjectType(
                    th.Property(
                        "extractor_namespace",
                        th.StringType,
                        description="Extractor namespace which contains the stream to be moved to Notion database.",
                        required=True,
                    ),
                    th.Property(
                        "stream_name",
                        th.StringType,
                        description="Name of the input stream to be moved to Notion database.",
                        required=True,
                    ),
                    th.Property(
                        "database_id",
                        th.StringType,
                        description="Id of the Notion database to be used.",
                        required=True,
                    ),
                    nullable=False,
                ),
            ),
            required=True,
            description="List of streams to be moved to Notion database.",
        ),
        th.Property(
            "api_key",
            th.StringType(nullable=False),
            secret=True,  # Flag config as protected.
            required=True,
            description="Notion api key",
        ),
    ).to_dict()

    default_sink_class = notionSink


if __name__ == "__main__":
    Targetnotion.cli()
