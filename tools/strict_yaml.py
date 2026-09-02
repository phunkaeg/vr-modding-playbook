"""Shared YAML loader that rejects duplicate mapping keys.

PyYAML's default loaders silently keep the last value for a duplicate key.
That behaviour is unsafe for evidence ledgers: one review record can erase
another while every downstream generator still succeeds.
"""

from __future__ import annotations

from typing import Any

import yaml
from yaml.constructor import ConstructorError


class UniqueKeyLoader(yaml.SafeLoader):
    """SafeLoader variant with mapping-key uniqueness enforced."""


def _construct_unique_mapping(
    loader: UniqueKeyLoader,
    node: yaml.MappingNode,
    deep: bool = False,
) -> dict[Any, Any]:
    loader.flatten_mapping(node)
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in mapping
        except TypeError as exc:
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"found an unhashable key ({key!r})",
                key_node.start_mark,
            ) from exc
        if duplicate:
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"found duplicate key {key!r}",
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def load_unique_yaml(text: str) -> Any:
    """Parse trusted-ledger YAML while making duplicate keys fatal."""
    return yaml.load(text, Loader=UniqueKeyLoader)
