from collections.abc import Sequence
from dataclasses import dataclass

from document_intelligence.model_provider.types import PageClassification


@dataclass(frozen=True)
class DocumentBoundary:
    """One contiguous run of Pages destined to become one Document (CONTEXT.md's Document),
    found by grouping page-level Classification results (ADR-0001's page-level pass).

    `document_type_name` is `None` for a run of unclassified Pages, which still becomes its
    own Document rather than being dropped — the page-accounting invariant.
    """

    document_type_name: str | None
    page_indices: tuple[int, ...]


def group_pages_into_documents(
    page_classifications: Sequence[PageClassification],
) -> tuple[DocumentBoundary, ...]:
    """Split a Submission's per-Page classification results into Document boundaries.

    Consecutive Pages carrying the same Document Type group into one boundary (including
    consecutive unclassified Pages, keyed on `None`); a Document Type change — or a
    transition to/from unclassified — starts a new one. Keys on Document Type alone, never
    Schema version, so harmless per-page version disagreement within one Document Type can't
    split a real Document (`PageClassification` doesn't even carry a version — see ADR-0001).
    Every input Page index ends up in exactly one boundary, in order.
    """
    boundaries: list[DocumentBoundary] = []
    current_type: str | None = None
    current_indices: list[int] = []

    for index, classification in enumerate(page_classifications):
        document_type_name = classification.document_type_name
        if current_indices and document_type_name == current_type:
            current_indices.append(index)
            continue
        if current_indices:
            boundaries.append(DocumentBoundary(current_type, tuple(current_indices)))
        current_type = document_type_name
        current_indices = [index]

    if current_indices:
        boundaries.append(DocumentBoundary(current_type, tuple(current_indices)))

    return tuple(boundaries)
