import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from document_intelligence.model_provider.types import DocumentTypeSchema

_VERSION_FILE_PATTERN = re.compile(r"^v(\d+)\.json$")
_CONFIG_FILENAME = "config.json"


class SchemaRegistryError(Exception):
    """Raised when the Schema Registry fails to load, or a lookup can't be satisfied."""


@dataclass(frozen=True)
class RegisteredDocumentType:
    """One Document Type's Schema at one version, plus its Confidence Threshold.

    Confidence Threshold is shared by every version of a Document Type
    (ADR-0004) — it's set once per Document Type, not per Schema version.
    """

    schema: DocumentTypeSchema
    confidence_threshold: float


class SchemaRegistry:
    """The directory of Schema files loaded at startup. See README.md's "Schema Registry"
    section for the directory layout convention and the operator-enforced immutability invariant.
    """

    def __init__(self, entries: Mapping[str, Mapping[int, RegisteredDocumentType]]) -> None:
        self._entries: dict[str, dict[int, RegisteredDocumentType]] = {
            name: dict(versions) for name, versions in entries.items()
        }

    @classmethod
    def load(cls, directory: Path | str) -> "SchemaRegistry":
        root = Path(directory)
        if not root.is_dir():
            raise SchemaRegistryError(f"Schema Registry directory not found: {root}")

        entries = {
            type_dir.name: _load_document_type(type_dir)
            for type_dir in sorted(p for p in root.iterdir() if p.is_dir())
        }
        return cls(entries)

    def get(self, name: str, version: int | None = None) -> RegisteredDocumentType:
        versions = self._entries.get(name)
        if not versions:
            raise SchemaRegistryError(f"Unknown Document Type: {name}")

        if version is None:
            return versions[max(versions)]

        try:
            return versions[version]
        except KeyError:
            raise SchemaRegistryError(
                f"Document Type '{name}' has no Schema version {version}"
            ) from None

    def all_latest(self) -> Sequence[DocumentTypeSchema]:
        """Every Document Type at its latest version, as `ModelProvider.classify_page`/
        `classify_document` (protocol.py) take a `Sequence[DocumentTypeSchema]` of candidates.
        """
        return tuple(self.get(name).schema for name in sorted(self._entries))


def _load_document_type(type_dir: Path) -> dict[int, RegisteredDocumentType]:
    name = type_dir.name
    confidence_threshold = _load_confidence_threshold(type_dir, name)

    versions: dict[int, RegisteredDocumentType] = {}
    for path in sorted(type_dir.iterdir()):
        match = _VERSION_FILE_PATTERN.match(path.name)
        if not match:
            continue
        version = int(match.group(1))
        versions[version] = RegisteredDocumentType(
            schema=DocumentTypeSchema(
                name=name, schema_version=version, json_schema=_load_json(path)
            ),
            confidence_threshold=confidence_threshold,
        )

    if not versions:
        raise SchemaRegistryError(
            f"Document Type '{name}' has no Schema versions "
            "(expected files named v1.json, v2.json, ...)"
        )

    return versions


def _load_confidence_threshold(type_dir: Path, name: str) -> float:
    config_path = type_dir / _CONFIG_FILENAME
    if not config_path.is_file():
        raise SchemaRegistryError(
            f"Document Type '{name}' is missing required {_CONFIG_FILENAME} with a "
            "confidence_threshold (ADR-0004) — Document Types cannot be registered without one"
        )

    config = _load_json(config_path)
    threshold = config.get("confidence_threshold")
    if threshold is None:
        raise SchemaRegistryError(
            f"Document Type '{name}' is missing a required confidence_threshold in "
            f"{_CONFIG_FILENAME} (ADR-0004) — Document Types cannot be registered without one"
        )
    if not isinstance(threshold, int | float) or isinstance(threshold, bool):
        raise SchemaRegistryError(
            f"Document Type '{name}' has a non-numeric confidence_threshold in {_CONFIG_FILENAME}"
        )
    return float(threshold)


def _load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise SchemaRegistryError(f"Invalid JSON in {path}: {exc}") from exc
