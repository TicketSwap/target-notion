"""Tests standard target features using the built-in SDK tests library."""

from __future__ import annotations

import typing as t

from singer_sdk.testing import get_target_test_class

from target_notion.target import Targetnotion

# TODO: Initialize minimal target config
SAMPLE_CONFIG: dict[str, t.Any] = {}


# Run standard built-in target tests from the SDK:
StandardTargetTests = get_target_test_class(
    target_class=Targetnotion,
    config=SAMPLE_CONFIG,
)


class TestTargetnotion(StandardTargetTests):  # type: ignore[misc, valid-type]
    """Standard Target Tests."""


# TODO: Create additional tests as appropriate for your target.
