# Document Intelligence

A schema-based classification and extraction system: callers submit files, the system splits them into individual documents, classifies each against a registry of document types, and extracts structured fields according to the matched type's schema.

## Language

**Submission**:
The file a caller uploads via the API. May span many pages and may contain more than one Document.
_Avoid_: File, upload (as a domain term — fine as plain English, but the API/data model should say Submission).

**Document**:
One logical unit found by splitting a Submission — the thing that gets classified and, if matched, has fields extracted from it. A Job's Documents always form a complete partition of its Submission's Pages (unclassified runs of Pages become their own `unclassified` Document, never dropped). Moves through `pending` → `classified`/`unclassified` (terminal) → if classified, `extracted`/`extraction_failed` (terminal).
_Avoid_: Sub-document, logical document, file.

**Document Type**:
The category a Document is classified into (e.g. "Invoice", "Passport"). A Document Type is described formally by a Schema.
_Avoid_: Schema (when the type itself, rather than its formal definition, is meant).

**Schema**:
The formal JSON Schema definition of a Document Type's fields, used both as classification guidance and as the extraction target. Explicitly versioned; immutable once any Document has been processed against a given version.
_Avoid_: Document Type (when the formal artifact, not the category, is meant).

**Page**:
The atomic unit of a Submission — one page image. Pages are classified individually to find Document boundaries; a Document is a contiguous run of Pages.

**Classification**:
Determining a Document Type for a unit of content. Happens twice, at two granularities: once per-Page (against Document Type only, used purely to find Document boundaries via grouping), and once per-Document after grouping (against the full Schema, given all the Document's Pages together, to settle the authoritative Schema version used for extraction).
_Avoid_: Using "classification" unqualified when the Page-level vs Document-level distinction matters — say "page classification" or "document classification".

**Extraction**:
Pulling structured field data out of a classified Document, in one model call given all of the Document's Pages together, validated against the Document's bound Schema version. On validation failure, retried once with the validation errors fed back to the Provider; a second failure moves the Document to `extraction_failed`.

**Schema Registry**:
The directory of Schema files loaded at startup — the full set of Document Types the system currently knows how to classify against.

**Model Provider**:
The vendor whose model performs Classification and Extraction (e.g. Anthropic). The pipeline calls Providers only through a fixed internal interface, so a new Provider can be added without changing Classification/Extraction/splitting logic.
_Avoid_: LLM, vendor (as domain vocabulary — fine as plain English elsewhere).

**Job**:
The processing lifecycle of one Submission — created the moment a Submission is accepted, polled by the caller for status/results. Always one Job per Submission. Moves through `pending` → `processing` → `complete`; `complete` means every Document has reached a terminal state, regardless of whether any individual Document ended unclassified or extraction_failed. The Job status never encodes success/failure by itself — callers read per-Document status for that.
_Avoid_: Task, run (as the noun a caller polls for).
