"""Versioned ordinary-data serialization for immutable public results."""

from __future__ import annotations

import base64
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from enum import Enum
from typing import Any, TypeAlias, cast

from glyphkit.diagnostics import Diagnostic, DiagnosticSeverity, SourceRange
from glyphkit.embedding import EmbeddingUse, FontContainer, FontSubsetBundle, PortableFont
from glyphkit.errors import ConfigurationError
from glyphkit.fonts import EmbeddingPermission, FaceId, FontManifest, FontManifestEntry
from glyphkit.layout import Bounds, LineLayout, TextLayout, TextMeasurement
from glyphkit.math import (
    Accent,
    Delimited,
    ExtensionNode,
    Fraction,
    Limits,
    MathBox,
    MathRule,
    MathStyle,
    Matrix,
    Root,
    Script,
    Sequence,
    Symbol,
)
from glyphkit.outlines import (
    ClosePath,
    CubicTo,
    GlyphOutline,
    LineTo,
    MoveTo,
    Polyline,
    QuadraticTo,
    Transform2D,
)
from glyphkit.shaping import GlyphRun, PositionedGlyph
from glyphkit.unicode import TextDirection

JSONScalar: TypeAlias = bool | int | float | str | None
JSONValue: TypeAlias = JSONScalar | list["JSONValue"] | dict[str, "JSONValue"]

_CLASSES = (
    Accent,
    Bounds,
    ClosePath,
    CubicTo,
    Delimited,
    Diagnostic,
    ExtensionNode,
    FaceId,
    FontManifest,
    FontManifestEntry,
    FontSubsetBundle,
    Fraction,
    GlyphOutline,
    GlyphRun,
    Limits,
    LineLayout,
    LineTo,
    MathBox,
    MathRule,
    MathStyle,
    Matrix,
    MoveTo,
    Polyline,
    PortableFont,
    PositionedGlyph,
    QuadraticTo,
    Root,
    Script,
    Sequence,
    SourceRange,
    Symbol,
    TextLayout,
    TextMeasurement,
    Transform2D,
)
_ENUMS = (DiagnosticSeverity, EmbeddingPermission, EmbeddingUse, FontContainer, TextDirection)
_CLASS_REGISTRY = {item.__name__: item for item in _CLASSES}
_ENUM_REGISTRY = {item.__name__: item for item in _ENUMS}


def _encode(value: object) -> JSONValue:
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        if not (-float("inf") < value < float("inf")):
            raise ConfigurationError("non-finite floats cannot be serialized")
        return value
    if isinstance(value, bytes):
        return {"$bytes": base64.b64encode(value).decode("ascii")}
    if isinstance(value, Enum):
        return {"$enum": type(value).__name__, "value": str(value.value)}
    if isinstance(value, tuple):
        return {"$tuple": [_encode(item) for item in value]}
    if isinstance(value, frozenset):
        return {"$frozenset": [_encode(item) for item in sorted(value)]}
    if isinstance(value, Mapping):
        return {"$mapping": [[_encode(key), _encode(item)] for key, item in value.items()]}
    if is_dataclass(value) and not isinstance(value, type):
        result: dict[str, JSONValue] = {"$type": type(value).__name__}
        for field in fields(value):
            if not field.name.startswith("_"):
                result[field.name] = _encode(getattr(value, field.name))
        return result
    raise ConfigurationError(f"value is not serializable: {type(value).__name__}")


def _decode(value: JSONValue) -> object:
    if not isinstance(value, dict):
        return value
    if "$bytes" in value:
        encoded = value["$bytes"]
        if not isinstance(encoded, str):
            raise ConfigurationError("invalid base64 payload")
        return base64.b64decode(encoded, validate=True)
    if "$enum" in value:
        enum_name, enum_value = value["$enum"], value.get("value")
        if not isinstance(enum_name, str) or not isinstance(enum_value, str):
            raise ConfigurationError("invalid enum payload")
        enum_type = _ENUM_REGISTRY.get(enum_name)
        if enum_type is None:
            raise ConfigurationError(f"unknown enum type: {enum_name}")
        return enum_type(enum_value)
    for marker, factory in (("$tuple", tuple), ("$frozenset", frozenset)):
        if marker in value:
            items = value[marker]
            if not isinstance(items, list):
                raise ConfigurationError(f"invalid {marker[1:]} payload")
            return factory(_decode(item) for item in items)
    if "$mapping" in value:
        pairs = value["$mapping"]
        if not isinstance(pairs, list):
            raise ConfigurationError("invalid mapping payload")
        return {_decode(pair[0]): _decode(pair[1]) for pair in pairs if isinstance(pair, list)}
    kind = value.get("$type")
    if not isinstance(kind, str):
        return {key: _decode(item) for key, item in value.items()}
    registered = _CLASS_REGISTRY.get(kind)
    if registered is None:
        raise ConfigurationError(f"unknown serialized type: {kind}")
    target = cast(type[Any], registered)
    return target(**{key: _decode(item) for key, item in value.items() if key != "$type"})


def to_data(value: object) -> dict[str, JSONValue]:
    return {"schema_version": "1.0", "kind": type(value).__name__, "value": _encode(value)}


def from_data(kind: str, data: Mapping[str, JSONValue]) -> object:
    version = data.get("schema_version")
    if not isinstance(version, str) or version.split(".", 1)[0] != "1":
        raise ConfigurationError(f"unsupported serialization schema: {version!r}")
    if data.get("kind") != kind or "value" not in data:
        raise ConfigurationError(f"invalid serialized payload for {kind!r}")
    result = _decode(data["value"])
    if type(result).__name__ != kind:
        raise ConfigurationError(f"decoded kind does not match {kind!r}")
    return result
