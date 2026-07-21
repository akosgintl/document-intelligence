import json
from pathlib import Path

import pytest

from document_intelligence.schema_registry import (
    RegisteredDocumentType,
    SchemaRegistry,
    SchemaRegistryError,
)


def _write_document_type(
    root: Path,
    name: str,
    *,
    confidence_threshold: float | None = 0.8,
    versions: dict[int, dict] | None = None,
    write_config: bool = True,
) -> None:
    type_dir = root / name
    type_dir.mkdir()

    if write_config:
        config: dict = {}
        if confidence_threshold is not None:
            config["confidence_threshold"] = confidence_threshold
        (type_dir / "config.json").write_text(json.dumps(config))

    for version, schema in (versions or {1: {"title": name, "properties": {}}}).items():
        (type_dir / f"v{version}.json").write_text(json.dumps(schema))


def test_load_reads_a_directory_of_valid_schemas(tmp_path: Path):
    _write_document_type(
        tmp_path,
        "invoice",
        confidence_threshold=0.8,
        versions={1: {"title": "Invoice", "properties": {"invoiceNumber": {"type": "string"}}}},
    )

    registry = SchemaRegistry.load(tmp_path)
    entry = registry.get("invoice")

    assert entry == RegisteredDocumentType(
        schema=registry.get("invoice").schema,
        confidence_threshold=0.8,
    )
    assert entry.schema.name == "invoice"
    assert entry.schema.schema_version == 1
    assert entry.schema.json_schema == {
        "title": "Invoice",
        "properties": {"invoiceNumber": {"type": "string"}},
    }
    assert entry.confidence_threshold == 0.8


def test_get_defaults_to_the_latest_version(tmp_path: Path):
    _write_document_type(
        tmp_path,
        "invoice",
        versions={
            1: {"title": "Invoice v1"},
            2: {"title": "Invoice v2"},
            3: {"title": "Invoice v3"},
        },
    )

    registry = SchemaRegistry.load(tmp_path)

    latest = registry.get("invoice")
    assert latest.schema.schema_version == 3
    assert latest.schema.json_schema == {"title": "Invoice v3"}


def test_get_looks_up_an_explicit_version(tmp_path: Path):
    _write_document_type(
        tmp_path,
        "invoice",
        versions={1: {"title": "Invoice v1"}, 2: {"title": "Invoice v2"}},
    )

    registry = SchemaRegistry.load(tmp_path)

    v1 = registry.get("invoice", version=1)
    assert v1.schema.schema_version == 1
    assert v1.schema.json_schema == {"title": "Invoice v1"}

    v2 = registry.get("invoice", version=2)
    assert v2.schema.schema_version == 2


def test_every_version_of_a_document_type_shares_its_confidence_threshold(tmp_path: Path):
    _write_document_type(
        tmp_path,
        "invoice",
        confidence_threshold=0.65,
        versions={1: {"title": "Invoice v1"}, 2: {"title": "Invoice v2"}},
    )

    registry = SchemaRegistry.load(tmp_path)

    assert registry.get("invoice", version=1).confidence_threshold == 0.65
    assert registry.get("invoice", version=2).confidence_threshold == 0.65


def test_load_fails_loudly_when_confidence_threshold_is_missing(tmp_path: Path):
    _write_document_type(tmp_path, "invoice", confidence_threshold=None)

    with pytest.raises(SchemaRegistryError, match="confidence_threshold"):
        SchemaRegistry.load(tmp_path)


def test_load_fails_loudly_when_config_file_is_absent(tmp_path: Path):
    _write_document_type(tmp_path, "invoice", write_config=False)

    with pytest.raises(SchemaRegistryError, match="confidence_threshold"):
        SchemaRegistry.load(tmp_path)


def test_load_fails_loudly_on_invalid_json(tmp_path: Path):
    type_dir = tmp_path / "invoice"
    type_dir.mkdir()
    (type_dir / "config.json").write_text(json.dumps({"confidence_threshold": 0.8}))
    (type_dir / "v1.json").write_text("{not valid json")

    with pytest.raises(SchemaRegistryError):
        SchemaRegistry.load(tmp_path)


def test_load_fails_loudly_when_a_document_type_has_no_schema_versions(tmp_path: Path):
    type_dir = tmp_path / "invoice"
    type_dir.mkdir()
    (type_dir / "config.json").write_text(json.dumps({"confidence_threshold": 0.8}))

    with pytest.raises(SchemaRegistryError, match="no Schema versions"):
        SchemaRegistry.load(tmp_path)


def test_load_rejects_a_missing_registry_directory(tmp_path: Path):
    with pytest.raises(SchemaRegistryError):
        SchemaRegistry.load(tmp_path / "does-not-exist")


def test_get_raises_for_an_unknown_document_type(tmp_path: Path):
    _write_document_type(tmp_path, "invoice")
    registry = SchemaRegistry.load(tmp_path)

    with pytest.raises(SchemaRegistryError, match="passport"):
        registry.get("passport")


def test_get_raises_for_an_unknown_version(tmp_path: Path):
    _write_document_type(tmp_path, "invoice", versions={1: {"title": "Invoice v1"}})
    registry = SchemaRegistry.load(tmp_path)

    with pytest.raises(SchemaRegistryError, match="99"):
        registry.get("invoice", version=99)


def test_all_latest_returns_one_schema_per_document_type_at_its_latest_version(tmp_path: Path):
    _write_document_type(
        tmp_path,
        "invoice",
        versions={1: {"title": "Invoice v1"}, 2: {"title": "Invoice v2"}},
    )
    _write_document_type(tmp_path, "passport", versions={1: {"title": "Passport v1"}})

    registry = SchemaRegistry.load(tmp_path)
    latest = {schema.name: schema for schema in registry.all_latest()}

    assert set(latest) == {"invoice", "passport"}
    assert latest["invoice"].schema_version == 2
    assert latest["passport"].schema_version == 1
