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
            "database_id",
            th.StringType(nullable=False),
            description="ID of the parent page you want to create the database in",
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
