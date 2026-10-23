"""Tests standard target features using the built-in SDK tests library."""

from __future__ import annotations

import typing as t

from singer_sdk.testing import get_target_test_class
from singer_sdk.testing.suites import SingerTestSuite
from singer_sdk.testing.target_tests import (
    TargetCliPrintsTest,
    TargetInvalidSchemaTest,
    TargetRecordBeforeSchemaTest,
)

from target_notion.target import Targetnotion

SAMPLE_CONFIG: dict[str, t.Any] = {
    "streams": [
        {
            "extractor_namespace": "test",
            "stream_name": "test",
            "data_source_id": "00000000-0000-0000-0000-000000000000",
        },
    ],
    "api_key": "test",
}

StandardTargetTests = get_target_test_class(
    target_class=Targetnotion,
    config=SAMPLE_CONFIG,
    include_target_tests=False,
    custom_suites=[
        SingerTestSuite(
            kind="target",
            tests=[
                TargetCliPrintsTest,
                TargetInvalidSchemaTest,
                TargetRecordBeforeSchemaTest,
            ],
        ),
    ],
)


class TestTargetnotion(StandardTargetTests):  # type: ignore[misc, valid-type]
    """Standard Target Tests that never reach Notion."""
