"""Unit tests for the page-grouping/splitting algorithm (#23) — a pure function, tested
directly against `PageClassification` values with no API/DB involved, per this repo's
Testing Decisions."""

from document_intelligence.grouping import DocumentBoundary, group_pages_into_documents
from document_intelligence.model_provider.types import PageClassification


def _classifications(*document_type_names: str | None) -> list[PageClassification]:
    return [PageClassification(name) for name in document_type_names]


def test_empty_input_produces_no_boundaries():
    assert group_pages_into_documents([]) == ()


def test_single_page_produces_one_boundary():
    result = group_pages_into_documents(_classifications("invoice"))

    assert result == (DocumentBoundary("invoice", (0,)),)


def test_multiple_pages_of_the_same_type_are_not_fragmented():
    result = group_pages_into_documents(_classifications("invoice", "invoice", "invoice"))

    assert result == (DocumentBoundary("invoice", (0, 1, 2)),)


def test_a_document_type_change_starts_a_new_document():
    result = group_pages_into_documents(_classifications("invoice", "invoice", "receipt"))

    assert result == (
        DocumentBoundary("invoice", (0, 1)),
        DocumentBoundary("receipt", (2,)),
    )


def test_several_distinct_documents_back_to_back_each_split_out():
    result = group_pages_into_documents(
        _classifications("invoice", "invoice", "receipt", "receipt", "receipt")
    )

    assert result == (
        DocumentBoundary("invoice", (0, 1)),
        DocumentBoundary("receipt", (2, 3, 4)),
    )


def test_consecutive_unclassified_pages_group_into_one_unclassified_document():
    result = group_pages_into_documents(_classifications("invoice", None, None, "receipt"))

    assert result == (
        DocumentBoundary("invoice", (0,)),
        DocumentBoundary(None, (1, 2)),
        DocumentBoundary("receipt", (3,)),
    )


def test_a_single_unclassified_page_still_becomes_its_own_document():
    result = group_pages_into_documents(_classifications(None))

    assert result == (DocumentBoundary(None, (0,)),)


def test_the_same_type_separated_by_an_unclassified_run_is_not_merged_across_the_gap():
    result = group_pages_into_documents(_classifications("invoice", None, "invoice"))

    assert result == (
        DocumentBoundary("invoice", (0,)),
        DocumentBoundary(None, (1,)),
        DocumentBoundary("invoice", (2,)),
    )


def test_every_page_index_is_accounted_for_exactly_once():
    classifications = _classifications("invoice", "invoice", None, "receipt", "receipt", None)

    boundaries = group_pages_into_documents(classifications)

    seen_indices = [index for boundary in boundaries for index in boundary.page_indices]
    assert seen_indices == list(range(len(classifications)))


def test_grouping_keys_on_document_type_only_never_schema_version():
    # PageClassification (model_provider/types.py) carries no schema_version field at all —
    # page-level results structurally can't disagree on version, only on Document Type
    # (ADR-0001). This test documents that invariant at the grouping seam.
    assert not hasattr(PageClassification(None), "schema_version")
