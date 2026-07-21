# Document Intelligence

A schema-based classification and extraction system: callers submit files, the system splits them into individual documents, classifies each against a registry of document types, and extracts structured fields according to the matched type's schema.

## Language

**Submission**:
The file a caller uploads via the API. May span many pages and may contain more than one Document.
_Avoid_: File, upload (as a domain term — fine as plain English, but the API/data model should say Submission).

**Document**:
One logical unit found by splitting a Submission — the thing that gets classified and, if matched, has fields extracted from it. A Job's Documents always form a complete partition of its Submission's Pages (unclassified runs of Pages become their own `unclassified` Document, never dropped). Moves through `pending` → `classified`/`unclassified`/`classification_needs_review` (terminal) → if `classified`, `extracted`/`extraction_failed`/`extraction_needs_review` (terminal). Terminal means the automated pipeline is done with the Document — for most terminal statuses that's final, but a `classification_needs_review`, `extraction_needs_review`, or `extraction_failed` Document can still be moved onward by a Review.
_Avoid_: Sub-document, logical document, file.

**Document Type**:
The category a Document is classified into (e.g. "Invoice", "Passport"). A Document Type is described formally by a Schema.
_Avoid_: Schema (when the type itself, rather than its formal definition, is meant).

**Schema**:
The formal JSON Schema definition of a Document Type's fields, used both as classification guidance and as the extraction target. Explicitly versioned — a plain incrementing integer scoped per Document Type, not semver — and immutable once any Document has been processed against a given version.
_Avoid_: Document Type (when the formal artifact, not the category, is meant).

**Page**:
The atomic unit of a Submission — one page image. Pages are classified individually to find Document boundaries; a Document is a contiguous run of Pages.

**Classification**:
Determining a Document Type for a unit of content. Happens twice, at two granularities: once per-Page (against Document Type only, used purely to find Document boundaries via grouping — never Confidence-gated), and once per-Document after grouping (against the full Schema, given all the Document's Pages together, to settle the authoritative Schema version used for extraction). The document-level pass produces a Confidence for the assigned Document Type; below the matched Schema's Confidence Threshold, the Document lands in `classification_needs_review` instead of `classified` — as does a Document whose document-level Classification call exhausted its transient-error retry budget without a low-confidence result to blame (see ADR-0009).
_Avoid_: Using "classification" unqualified when the Page-level vs Document-level distinction matters — say "page classification" or "document classification".

**Extraction**:
Pulling structured Field data out of a classified Document, in one model call given all of the Document's Pages together, validated against the Document's bound Schema version. On validation failure, retried once with the validation errors fed back to the Provider; a second failure moves the Document to `extraction_failed`. Each extracted Field carries its own Confidence; if any Field's Confidence falls below the bound Schema's Confidence Threshold, the Document moves to `extraction_needs_review` instead of `extracted` — as does a Document whose Extraction call exhausted its transient-error retry budget before ever producing a validatable result (see ADR-0009).

**Field**:
One top-level property of a Document Type's Schema — the unit Extraction produces a value for, and that Confidence and Review each address individually. A Field's own nested structure (e.g. an array of line items) isn't decomposed further: Confidence and Review operate on the Field as a whole, not on values nested inside it.
_Avoid_: Property (as domain vocabulary, when a Schema's top-level Field is meant — fine as plain English for JSON Schema structure generally).

**Confidence**:
A score in [0,1] the Model Provider attaches to a single decision — the Document Type assigned at document-level Classification, or one Field value produced at Extraction. Layered, not a single number per Document: a Document has one Classification Confidence and, once extracted, one Confidence per extracted Field. Obtained via the Provider's self-reported certainty — emitted as a field in the same Classification/Extraction call, at no extra cost — not via token-probability/logprobs (not exposed by the Provider's API) or repeated-sampling agreement (a real technique, deferred pending evidence self-reported confidence needs augmenting; see ADR-0008).

**Confidence Threshold**:
The per-Document-Type cutoff below which a Classification or Extraction result isn't auto-finalized — one shared value gates both, not split per-concern or per-Field. Set by the platform operator as separate metadata attached to the Document Type, independently mutable from Schema versioning — not baked into the immutable Schema JSON, so retuning sensitivity never requires minting a new Schema version. Required at registration: no Document Type can be registered without one, and no system-wide default exists. Crossing it below threshold routes the Document to `classification_needs_review` or `extraction_needs_review` instead of its normal terminal status.

**Review**:
The caller-driven resolution of a Document stuck in `classification_needs_review`, `extraction_needs_review`, or `extraction_failed` — the only way a terminal Document status changes after the fact. Performed via API by the caller's own side; this system provides no reviewer team or UI of its own. A classification resolution assigns a Document Type (bound to that Type's latest Schema version) to the Document's existing Pages, or confirms `unclassified`, without altering Document boundaries — the resolved Document then proceeds through automated Extraction exactly like any other `classified` Document. An extraction resolution (from `extraction_needs_review` or `extraction_failed`) submits a complete replacement Field set, validated against the bound Schema exactly like automated Extraction; a validation failure moves the Document straight to `extraction_failed`, with no retry. Resolution is a stateless status transition — no Reviewer identity or Review history is recorded — and resolving a Document after its Job has already reached `complete` never changes the Job's status.
_Avoid_: Human-in-the-loop, HITL (as domain vocabulary — fine as plain English elsewhere).

**Schema Registry**:
The directory of Schema files loaded at startup — the full set of Document Types the system currently knows how to classify against.

**Model Provider**:
The vendor whose model performs Classification and Extraction (e.g. Anthropic). The pipeline calls Providers only through a fixed internal interface, so a new Provider can be added without changing Classification/Extraction/splitting logic.
_Avoid_: LLM, vendor (as domain vocabulary — fine as plain English elsewhere).

**Model Call**:
One completed call through the Model Provider interface — page Classification, document Classification, or Extraction — persisted with its prompt, response, token usage, and latency, linked to the Job it was made for. Captured once, at the Provider-interface seam itself, so every call site (current and future) is traced without adding logging of its own. Exists so an operator can debug a specific misclassification/extraction after the fact and see what a Job cost; not itself part of the processing pipeline's decision-making.

**Job**:
The processing lifecycle of one Submission — created the moment a Submission is accepted, polled by the caller for status/results. Always one Job per Submission. Moves through `pending` → `processing` → `complete` | `failed`. `complete` means every Document has reached a terminal state, regardless of whether any individual Document ended unclassified, extraction_failed, or needing Review — the Job status never encodes per-Document success/failure by itself; callers read per-Document status for that. `failed` is a different kind of outcome: the pipeline itself couldn't finish processing the Submission (an infrastructure-level failure, e.g. a worker crashing repeatedly, after exhausting bounded recovery attempts) — not a statement about any individual Document's content. Documents that reached a terminal status before the failure remain visible in the Job's result even when the Job itself is `failed`. A `complete` Job can still have Documents sitting in `classification_needs_review`/`extraction_needs_review`/`extraction_failed` awaiting a Review — resolving one after the fact never reopens or otherwise changes the Job's status.
_Avoid_: Task, run (as the noun a caller polls for).
