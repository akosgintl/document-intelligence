# JSON Schema design for Classification, Extraction, and Validation

**Scope.** This document researches, from primary sources only (the JSON Schema specification and Anthropic's official API docs), what JSON Schema itself provides — and what it explicitly does *not* provide — for each of this system's three tasks: **Classification**, **Extraction**, and **Validation**. For each task it covers (a) how the task's target is *defined* as a Schema, and (b) the *shape of the task's result*. Every claim below is cited to a specific spec section or docs page that was fetched directly; nothing is asserted from memory alone.

## Summary of findings

- **Draft currency.** [json-schema.org/specification](https://json-schema.org/specification) states outright: "The current version is *2020-12*!" As of this research (July 2026), **draft 2020-12 remains the only published, stable JSON Schema draft** — there is no newer stabilized draft. [json-schema.org/specification-links](https://json-schema.org/specification-links) lists a "Draft 2021-NN *(TBD)*" placeholder for a future draft, confirming work is in progress but nothing has shipped past 2020-12. This research is centered on draft 2020-12 as instructed, and that choice is still current.
- **JSON Schema has no native "classification" or "extraction" concept.** Both are this system's own tasks, built on top of the Schema Registry and the Model Provider. JSON Schema only supplies the *target shape* (a Schema) that a Provider is steered toward; the task semantics (pick one Document Type vs. populate all fields) are external.
- **JSON Schema's closest built-in "result shape" is Output Formatting** (draft 2020-12 Core spec, §12), which defines Flag/Basic/Detailed/Verbose formats for *validation* results only — not classification or extraction results.
- **JSON Schema has no native concept of confidence, fuzziness, or partial-match.** This is confirmed by the spec's own text on `format` (annotation vs. assertion) and is otherwise silent. Any confidence/fuzzy-validation result shape in this document is explicitly this repo's own invention.
- **Anthropic's `input_schema` on a tool is literally "a JSON Schema object"** — Claude's Messages API steers structured output (for both classification-style and extraction-style tasks) by attaching a JSON Schema to a tool definition and reading the `tool_use` block Claude returns.
- **Anthropic's docs do describe a validation-failure feedback/retry pattern**, but at the tool-call level (`is_error` on a `tool_result`, causing Claude to retry the call), not as a documented pattern specifically for "extracted JSON failed downstream Schema validation." This repo's own retry-once-with-errors-fed-back design for Extraction is a specialization of that general mechanism, not something Anthropic documents as an extraction-specific recipe. Details in the Extraction section below.
- **Docs-hosting note:** `docs.anthropic.com` no longer serves docs directly. Fetching `https://docs.anthropic.com/en/docs/build-with-claude/tool-use/overview` returns a `301` to `https://platform.claude.com/docs/en/docs/build-with-claude/tool-use/overview`, and `https://docs.claude.com/en/docs/...` returns a `302` to the equivalent `https://platform.claude.com/docs/en/...` path. **The current canonical host for Anthropic's official docs is `platform.claude.com`**, not `docs.claude.com`. All Anthropic citations below use the resolved `platform.claude.com` URLs.

---

## 1. Classification

### What JSON Schema contributes

JSON Schema itself defines no "classification" keyword or task. In this system, Classification means: given a Page or a Document, pick the single Document Type (and, for per-Document classification, the specific Schema version) it belongs to. JSON Schema's only role is supplying the **Schema Registry's per-Document-Type Schemas** as the menu of possible target shapes, and — for per-Document classification — the *chosen* Schema's `title`/`description`/`properties` as guidance text the Provider reasons over.

### Defining a Document Type's Schema for classification guidance

A Document Type's Schema (draft 2020-12) doubles as classification guidance: its `$id`, `title`, and `description` are exactly what a Provider needs to distinguish one Document Type from another, using ordinary JSON Schema Validation-spec keywords (`type` — Validation spec §6.1.1; `properties`/`required` — Core spec §10.3.2 / Validation spec §6.5.3, all fetched from [json-schema.org/draft/2020-12/json-schema-core](https://json-schema.org/draft/2020-12/json-schema-core) and [json-schema.org/draft/2020-12/json-schema-validation](https://json-schema.org/draft/2020-12/draft-bhutton-json-schema-validation-01.html)):

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://document-intelligence.example/schemas/invoice/v3",
  "title": "Invoice",
  "description": "A vendor-issued invoice requesting payment for goods or services delivered. Distinguishing marks: an invoice number, a bill-to party, and one or more line items with unit prices.",
  "type": "object",
  "properties": {
    "invoiceNumber": { "type": "string", "description": "Unique invoice identifier printed on the document." },
    "issueDate": { "type": "string", "format": "date" },
    "billTo": { "type": "string" },
    "lineItems": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "description": { "type": "string" },
          "quantity": { "type": "number" },
          "unitPrice": { "type": "number" }
        },
        "required": ["description", "quantity", "unitPrice"]
      }
    },
    "totalAmount": { "type": "number" }
  },
  "required": ["invoiceNumber", "billTo", "lineItems", "totalAmount"]
}
```

Nothing above is a classification-specific keyword — `title`/`description` are ordinary annotation keywords defined in the Validation spec's metadata section; they are simply the fields this system's Provider prompt repurposes as classification guidance.

### The shape of a classification result — **this repo's own design**

JSON Schema defines no output shape for "which Document Type does this match." The nearest primary-source mechanism for getting a *constrained, machine-parseable* choice out of the Model Provider is Anthropic's **tool use**: a tool definition carries an `input_schema` that "is a [JSON Schema](https://json-schema.org/) object defining the expected parameters for the tool," and Claude's response contains a `tool_use` content block with `id`, `name`, and `input` conforming to that schema — confirmed on the "Define tools" page ([platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools)) and the "Handle tool calls" page ([platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls)), which shows the exact `tool_use` block shape:

```json
{
  "type": "tool_use",
  "id": "toolu_01A09q90qw90lq917835lq9",
  "name": "get_weather",
  "input": { "location": "San Francisco, CA", "unit": "celsius" }
}
```

A classification tool for this system would define an `input_schema` whose `enum` lists the known Document Type names (drawn from the Schema Registry) — `enum` is a Validation-spec keyword (§6.1.2, same page as above: "An instance validates successfully against this keyword if its value is equal to one of the elements in this keyword's array value"). Reading the resulting `tool_use.input` off that schema, this system's own classification-result envelope (**not a JSON Schema or Anthropic-mandated shape — this repo's invention**) might look like:

```json
{
  "documentTypeName": "Invoice",
  "schemaVersion": "v3",
  "matched": true
}
```

For per-Page classification (Document Type only, no Schema version) the envelope would omit `schemaVersion`; for per-Document classification (run after Page grouping, per the two-phase design) `schemaVersion` is populated because settling one authoritative Schema version is the entire point of that second pass. Both of these envelope shapes, and the `matched`/`unclassified` outcome field, are this system's own invention — JSON Schema and Anthropic's API define the *building blocks* (`enum`, `tool_use.input`) but not this envelope.

---

## 2. Extraction

### Defining an extraction target Schema

Extraction reuses the same per-Document-Type Schema as classification (the "Schema...used both as classification guidance and as the extraction target" per this system's own vocabulary) — but for Extraction, the *field-level* keywords (`type`, `required`, `format`, nested `properties`) are what matter, not just `title`/`description`. The Invoice Schema shown above is exactly what would be handed to the Provider as extraction target — every `properties` entry becomes a field the Provider must populate.

### How the Schema is passed to the Model Provider

Anthropic's tool-use mechanism is the same one used for Classification: `input_schema` is "a JSON Schema object defining the expected parameters for the tool" (["Define tools"](https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools)). For Extraction, the Invoice Schema's `properties`/`required`/nested-object structure is placed directly as the tool's `input_schema`, and the tool-use system prompt Anthropic constructs literally embeds "Here are the functions available in JSONSchema format: {{ TOOL DEFINITIONS IN JSON SCHEMA }}" — quoted verbatim from the "Tool use system prompt" section of the same page. Anthropic also offers a parallel, non-tool mechanism — **structured outputs** (`output_config.format` with `type: "json_schema"`) — described on [platform.claude.com/docs/en/build-with-claude/structured-outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) as guaranteeing "schema-compliant responses through constrained decoding," with the tradeoff that Anthropic's supported JSON Schema subset for both `input_schema` (with `strict: true`) and `output_config.format` excludes several Validation-spec keywords this system might otherwise want on an extraction Schema — per that same page, **not supported**: numeric constraints (`minimum`, `maximum`, `multipleOf`), string-length constraints (`minLength`, `maxLength`), recursive schemas, external `$ref`, and `additionalProperties` values other than `false`. This is an Anthropic API-level limitation, not a JSON Schema spec limitation — the full Schema (with those constraints) is still what this system's own downstream Validation step checks the extracted output against.

### The shape of an extraction result

Claude's `tool_use.input` *is* the extracted JSON object, already shaped to (Anthropic's constrained subset of) the target Schema — this is a real, documented mechanism, not invented:

```json
{
  "type": "tool_use",
  "id": "toolu_01Extract000000000000001",
  "name": "extract_invoice_fields",
  "input": {
    "invoiceNumber": "INV-10293",
    "issueDate": "2026-06-30",
    "billTo": "Acme Corp",
    "lineItems": [
      { "description": "Widget", "quantity": 4, "unitPrice": 12.5 }
    ],
    "totalAmount": 50.0
  }
}
```

What this system does *around* that `input` — wrapping it in an extraction-result envelope with Document identity, the bound Schema version, and a validation outcome — is **this repo's own design**, e.g.:

```json
{
  "documentId": "doc_8f2a...",
  "schemaId": "https://document-intelligence.example/schemas/invoice/v3",
  "extractedFields": { "...": "the tool_use.input object above" },
  "attempt": 1,
  "status": "extracted"
}
```

### Anthropic's docs on a validation-failure retry/feedback loop

This system's design retries Extraction once, feeding validation errors back to the Provider, before moving the Document to `extraction_failed`. Anthropic's own docs **do** describe a structurally identical mechanism, but scoped to malformed *tool calls*, not to downstream Schema-validation failures of already-well-formed extracted data. From "Handle tool calls" → "Handling errors with is_error" → "Invalid tool name" ([platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls)):

> "If Claude's attempted use of a tool is invalid (for example, missing required parameters)... you can also continue the conversation forward with a `tool_result` that indicates the error, and Claude will try to use the tool again with the missing information filled in... If a tool request is invalid or missing parameters, Claude will retry 2-3 times with corrections before apologizing to the user."

with the example payload:

```json
{
  "role": "user",
  "content": [
    {
      "type": "tool_result",
      "tool_use_id": "toolu_01A09q90qw90lq917835lq9",
      "content": "Error: Missing required 'location' parameter",
      "is_error": true
    }
  ]
}
```

That page also directly recommends, in a callout on the same accordion: "To eliminate invalid tool calls entirely, use strict tool use with `strict: true`... This guarantees that tool inputs will always match your schema exactly, preventing missing parameters and type mismatches" — i.e. Anthropic's own recommended fix for *malformed* tool input is `strict: true`, not a retry loop.

**What Anthropic's docs do not say:** nowhere in the fetched pages (`tool-use/handle-tool-calls`, `tool-use/define-tools`, `build-with-claude/structured-outputs`) is there guidance for the specific case this system faces — a syntactically well-formed `tool_use.input` that nonetheless fails a *richer* downstream JSON Schema validation pass (e.g. a `format` or cross-field business rule beyond what `strict: true` enforces). The `is_error`/`tool_result` retry mechanism is generic enough to be reused for that purpose (feed the Schema validation errors back as `tool_result` content with `is_error: true`), but Anthropic's docs describe it only for structurally-invalid tool calls, not for this system's specific "retry extraction once with validation errors" policy. **That policy, and the choice to retry exactly once before moving to `extraction_failed`, is this repo's own design decision** — it borrows Anthropic's documented retry *mechanism* but is not itself a documented Anthropic recipe for extraction validation.

---

## 3. Validation

Validation is split, per the task brief, along two axes: **single-field vs. cross-field** (what a rule is *about*) and **deterministic vs. fuzzy** (how confidently a rule can be checked).

### 3a. Single-field validation (deterministic)

Ordinary Validation-spec assertion keywords apply to one field/value at a time. Fetched directly from [json-schema.org/draft/2020-12/json-schema-validation](https://json-schema.org/draft/2020-12/draft-bhutton-json-schema-validation-01.html):

- **`type`** (§6.1.1): "String values MUST be one of the six primitive types ('null', 'boolean', 'object', 'array', 'number', or 'string'), or 'integer' which matches any number with a zero fractional part."
- **`required`** (§6.5.3): "An object instance is valid against this keyword if every item in the array is the name of a property in the instance."
- **`format`** (§7.1, Foreword): "The value of this keyword is called a format attribute... a format attribute can generally only validate a given set of instance types." Its assertion behavior is opt-in — see §3d below.

Example, on the Invoice Schema:

```json
{ "totalAmount": { "type": "number" }, "issueDate": { "type": "string", "format": "date" } }
```

### 3b. Cross-field validation (deterministic)

These are the keywords the spec provides specifically for rules that span *more than one field*. All quotes below are fetched directly from the Core spec ([json-schema.org/draft/2020-12/json-schema-core](https://json-schema.org/draft/2020-12/json-schema-core)) or Validation spec.

- **`dependentRequired`** (Validation spec §6.5.4): "This keyword specifies properties that are required if a specific other property is present... Validation succeeds if, for each name that appears in both the instance and as a name within this keyword's value, every item in the corresponding array is also the name of a property in the instance." — buys you "if field A is present, fields B and C must also be present," e.g. `"dependentRequired": {"purchaseOrderNumber": ["approverName"]}` on the Invoice Schema (if a PO number is given, an approver name must be too).
- **`dependentSchemas`** (Core spec §10.2.2.4): "This keyword specifies subschemas that are evaluated if the instance is an object and contains a certain property... If the object key is a property in the instance, the entire instance must validate against the subschema." — a strictly more powerful sibling of `dependentRequired`: instead of just requiring other properties, it can impose *any* schema (types, ranges, more `required`) conditioned on one property's presence. E.g. `"dependentSchemas": {"discountApplied": {"required": ["discountReason"], "properties": {"discountReason": {"minLength": 5}}}}`.
- **`if`/`then`/`else`** (Core spec §10.2.2.1–10.2.2.3): "Instances that successfully validate against this keyword's subschema MUST also be valid against the subschema value of the 'then' keyword, if present... Instances that fail to validate against this keyword's subschema MUST also be valid against the subschema value of the 'else' keyword, if present." — buys you conditional cross-field logic keyed on *any* condition (not just presence), e.g. "if `documentType` is `credit-note`, then `totalAmount` must be negative; else it must be positive."
- **`allOf`/`anyOf`/`oneOf`/`not`** (Core spec §10.2.1.1–10.2.1.4): `allOf` — "An instance validates successfully against this keyword if it validates successfully against all schemas defined by this keyword's value" (AND-combine independently written cross-field rule blocks); `anyOf` — "at least one"; `oneOf` — "exactly one" (useful for "exactly one of these mutually exclusive field combinations must hold," e.g. either a `purchaseOrderNumber` block or a `creditNoteReference` block, never both); `not` — "An instance is valid against this keyword if it fails to validate successfully against the schema defined by this keyword" (forbid a field combination, e.g. `lineItems` non-empty AND `totalAmount` equal to `0`).
- **`unevaluatedProperties`** (Core spec §11.3, in "A Vocabulary for Unevaluated Locations"): "Validation with 'unevaluatedProperties' applies only to the child values of instance names that do not appear in the 'properties', 'patternProperties', 'additionalProperties', or 'unevaluatedProperties' annotation results... validation succeeds if the child instance validates against the 'unevaluatedProperties' schema." — buys you a closed-object check that correctly accounts for properties allowed by *sibling* `allOf`/`if`/`$ref` branches, which plain `additionalProperties` cannot do (it only sees the local `properties` list). This matters once cross-field `allOf`/`if` branches contribute their own conditionally-allowed properties.
- **`propertyNames`** (Core spec §10.3.2.4): "If the instance is an object, this keyword validates if every property name in the instance validates against the provided schema." — a constraint *between* the set of field names present, not any one field's value; e.g. enforcing a naming convention across whatever dynamic line-item keys appear.
- **`$ref`-based composition** (Core spec §8.2.3.1): "The '$ref' keyword is an applicator that is used to reference a statically identified schema. Its results are the results of the referenced schema... other keywords can appear alongside of '$ref' in the same schema object." — lets a cross-field rule block (e.g. a shared "billing address must match shipping country" `allOf` clause) be defined once in `$defs` and referenced from multiple Document Type Schemas, rather than duplicated.

Worked example combining several of the above on the Invoice Schema:

```json
{
  "allOf": [
    {
      "if": { "properties": { "documentSubtype": { "const": "credit-note" } } },
      "then": { "properties": { "totalAmount": { "exclusiveMaximum": 0 } } },
      "else": { "properties": { "totalAmount": { "exclusiveMinimum": 0 } } }
    }
  ],
  "dependentRequired": { "discountApplied": ["discountReason"] }
}
```

### 3c. The validation-result shape — spec-defined baseline (Output Formatting)

This is the one place in this whole document where JSON Schema *does* define a standardized result shape. Fetched directly from Core spec §12 ("Output Formatting") at [json-schema.org/draft/2020-12/json-schema-core](https://json-schema.org/draft/2020-12/json-schema-core):

> §12.2, "Output Formats": "This specification defines four output formats... **Flag** - A boolean which simply indicates the overall validation result with no further details. **Basic** - Provides validation information in a flat list structure. **Detailed** - Provides validation information in a condensed hierarchical structure based on the structure of the schema. **Verbose** - Provides validation information in an uncondensed hierarchical structure that matches the exact structure of the schema."

> §12.3, "Minimum Information": every sub-result should carry — §12.3.1 **`keywordLocation`** ("The relative location of the validating keyword that follows the validation path... expressed as a JSON Pointer"); §12.3.2 **`absoluteKeywordLocation`** ("The absolute, dereferenced location of the validating keyword... a full URI... This information MAY be omitted only if either the dynamic scope did not pass over a reference or if the schema does not declare an absolute URI as its '$id'"); §12.3.3 **`instanceLocation`** ("The location of the JSON value within the instance being validated... a JSON Pointer"); §12.3.4 the error-or-annotation value itself, keyed `"error"` for failures and `"annotation"` for successes; §12.3.5 nested results, keyed `"errors"` / `"annotations"` (plural) for the hierarchical formats.

> §12.4, "Output Structure": "The output MUST be an object containing a boolean property named 'valid'. When additional information about the result is required, the output MUST also contain 'errors' or 'annotations' as described below."

The spec's own worked example uses this schema and instance (§12.4, verbatim):

```json
{
  "$id": "https://example.com/polygon",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$defs": {
    "point": {
      "type": "object",
      "properties": { "x": { "type": "number" }, "y": { "type": "number" } },
      "additionalProperties": false,
      "required": ["x", "y"]
    }
  },
  "type": "array",
  "items": { "$ref": "#/$defs/point" },
  "minItems": 3
}
```
```json
[ { "x": 2.5, "y": 1.3 }, { "x": 1, "z": 6.7 } ]
```

**Flag** (§12.4.1) — spec's exact example: `{ "valid": false }`.

**Basic** (§12.4.2) — spec's exact example (flat list of output units):

```json
{
  "valid": false,
  "errors": [
    { "keywordLocation": "", "instanceLocation": "", "error": "A subschema had errors." },
    {
      "keywordLocation": "/items/$ref",
      "absoluteKeywordLocation": "https://example.com/polygon#/$defs/point",
      "instanceLocation": "/1",
      "error": "A subschema had errors."
    },
    {
      "keywordLocation": "/items/$ref/required",
      "absoluteKeywordLocation": "https://example.com/polygon#/$defs/point/required",
      "instanceLocation": "/1",
      "error": "Required property 'y' not found."
    },
    {
      "keywordLocation": "/items/$ref/additionalProperties",
      "absoluteKeywordLocation": "https://example.com/polygon#/$defs/point/additionalProperties",
      "instanceLocation": "/1/z",
      "error": "Additional property 'z' found but was invalid."
    },
    { "keywordLocation": "/minItems", "instanceLocation": "", "error": "Expected at least 3 items but found 2" }
  ]
}
```

**Detailed** (§12.4.3, spec's own description): "based on the schema and can be more readable for both humans and machines... Nodes that have no children are removed. Nodes that have a single child are replaced by the child." Its example nests the two `/1`-instance errors (missing `y`, disallowed `z`) under their shared `/items/$ref` node, next to the sibling `/minItems` error — the spec's stated benefit is that "the correlation is more easily identified" versus the flat Basic list.

**Verbose** (§12.4.4) — "a fully realized hierarchy that exactly matches that of the schema... it is RECOMMENDED that each node also carry a `valid` property." The spec links a full example at [json-schema.org/draft/2020-12/output/verbose-example](https://json-schema.org/draft/2020-12/output/verbose-example); a condensed excerpt (fetched directly) for a smaller schema/instance:

```json
{
  "valid": false,
  "keywordLocation": "",
  "instanceLocation": "",
  "errors": [
    { "valid": true, "keywordLocation": "/type", "instanceLocation": "" },
    { "valid": true, "keywordLocation": "/properties", "instanceLocation": "" },
    { "valid": false, "keywordLocation": "/additionalProperties", "instanceLocation": "" }
  ]
}
```

An implementation-note from §12.2 worth carrying into any implementation choice: "An implementation SHOULD provide at least one of the 'flag', 'basic', or 'detailed' format and MAY provide the 'verbose' format. If it provides one or more of the 'detailed' or 'verbose' formats, it MUST also provide the 'flag' format."

**Framing for this system:** the four formats above *are* spec-mandated — any validator conforming to draft 2020-12 output formatting produces one of these shapes. If this system's own validation-result envelope wraps one of these (e.g. adds a `documentId` or `attempt` number alongside a `"basic"`-format `errors` array), that wrapping is this repo's own addition layered on top of a genuine spec mechanism — call out explicitly which part is which if/when such an envelope is implemented.

### 3d. Fuzzy / confidence-based validation — **explicit spec gap**

JSON Schema, across both the Core and Validation specs fetched for this research, has **no native concept of confidence, fuzziness, partial-match, or probabilistic validity**. Every assertion keyword in the Validation spec produces a strict boolean (valid/invalid) contribution to the overall `valid` result described in §12.4 above. This is a real gap in the spec, not an oversight in this research — three lines of evidence:

1. **`format`'s annotation-only-by-default behavior is the closest the spec comes to "soft" checking, and it is still binary, not fuzzy.** From the Validation spec, §7.2.1 "Format-Annotation Vocabulary" ([json-schema.org/draft/2020-12/json-schema-validation](https://json-schema.org/draft/2020-12/draft-bhutton-json-schema-validation-01.html)): "The value of format MUST be collected as an annotation, if the implementation supports annotation collection... Implementations MAY still treat 'format' as an assertion in addition to an annotation... The implementation MUST provide options to enable and disable such evaluation and **MUST be disabled by default**." The opt-in assertion behavior is the **Format-Assertion vocabulary** (§7.2.2): "When the Format-Assertion vocabulary is declared with a value of true, implementations MUST provide full validation support for all of the formats... MUST evaluate 'format' as an assertion." Even when enabled, the result is still pass/fail — there is no partial-credit or confidence score anywhere in this mechanism.
2. **The spec's own intended extension point for anything beyond its built-in vocabularies is custom vocabularies, not sibling metadata.** `$vocabulary` (Core spec §8.1.2) is "used in meta-schemas to identify the vocabularies available for use in schemas described by that meta-schema... Together, this information forms a dialect." A confidence/fuzzy-match keyword would, per the spec's own design, be defined as a new custom vocabulary declared via `$vocabulary` in a custom meta-schema — the same mechanism that lets `$dynamicRef`/`$dynamicAnchor` (Core spec §8.2.2, §8.2.3.2) support "a cooperative extension mechanism... primarily useful with recursive schemas." Nothing in the fetched spec text suggests fuzziness/confidence as a motivating use case for `$vocabulary` or `$dynamicRef` — those sections discuss extensibility and recursive-schema reuse, not confidence scoring. The spec simply provides the *general* extensibility mechanism; it does not sketch a confidence vocabulary.
3. **Nothing in the fetched spec pages mentions "confidence," "fuzzy," "probability," or "partial" in connection with validation results.** The gap is confirmed by absence across every section read for this research (Core §8, §10, §11, §12; Validation §6, §7).

**Consequence, stated plainly:** any result shape this system uses to represent a fuzzy/confidence-scored field match (e.g. "the extracted `billTo` value is 85% likely to be a correct match for the Schema's expected format, given OCR noise") is **entirely this repo's own invention**. It is not a JSON Schema feature, not an Anthropic API feature, and not implied by any spec section cited above. An example of such a repo-invented shape, clearly not spec- or Anthropic-mandated:

```json
{
  "field": "billTo",
  "value": "Acme Corp",
  "schemaExpectation": { "type": "string" },
  "confidence": 0.85,
  "matchKind": "fuzzy",
  "note": "OCR ambiguity between 'Acme Corp' and 'Acme Corp.' — no spec-defined field for this; this repo's own convention."
}
```

The one legitimate, spec-sanctioned pattern that gets partway there without inventing new keywords is keeping such metadata **outside the schema, alongside the value, by external convention** — e.g. a sibling `_meta` object in the extraction result envelope (itself already established as this repo's own design in the Extraction section above) rather than a new assertion keyword inside the Schema document. That "sibling metadata, external convention" framing is explicitly one of the two extension paths this section was asked to evaluate, and it is the lower-effort one precisely because it does not require declaring a custom `$vocabulary` and meta-schema — but it is still not something the spec defines or endorses; it is simply *not prohibited*.

---

## Source index

| # | Source | URL |
|---|---|---|
| 1 | JSON Schema — Specification (draft-currency statement) | https://json-schema.org/specification |
| 2 | JSON Schema — Specification Links (draft list, future-draft placeholder) | https://json-schema.org/specification-links |
| 3 | JSON Schema Core, draft 2020-12 (§8 `$vocabulary`/`$dynamicRef`/`$dynamicAnchor`, §10 applicators, §11 `unevaluatedProperties`, §12 Output Formatting) | https://json-schema.org/draft/2020-12/json-schema-core |
| 4 | JSON Schema Validation, draft 2020-12 (§6 assertion keywords, §7 `format`) | https://json-schema.org/draft/2020-12/draft-bhutton-json-schema-validation-01.html |
| 5 | JSON Schema draft 2020-12 Verbose output example | https://json-schema.org/draft/2020-12/output/verbose-example |
| 6 | Anthropic — "Tool use with Claude" (overview, `tool_use`/`stop_reason`) | https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview |
| 7 | Anthropic — "Define tools" (`input_schema` as JSON Schema, tool-use system prompt) | https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools |
| 8 | Anthropic — "Handle tool calls" (`tool_use`/`tool_result`/`is_error`, invalid-tool-call retry) | https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls |
| 9 | Anthropic — "Structured outputs" (`output_config.format`, `strict` tool use, supported JSON Schema subset) | https://platform.claude.com/docs/en/build-with-claude/structured-outputs |

**Docs-hosting redirect chain observed during research:** `docs.anthropic.com/en/docs/build-with-claude/tool-use/overview` → 301 → `platform.claude.com/docs/en/docs/build-with-claude/tool-use/overview`; `docs.claude.com/en/docs/build-with-claude/tool-use/overview` → 302 → `platform.claude.com/docs/en/build-with-claude/tool-use/overview`. All citations above use the final `platform.claude.com` URLs actually fetched.
