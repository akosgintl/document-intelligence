# Computing Confidence against Anthropic's API

**Scope.** This document researches, from primary sources only (Anthropic's official API reference and product docs at `platform.claude.com`, and Anthropic's own first-party engineering blog at `anthropic.com/engineering`), how a system built on Anthropic's Claude API — using tool use / structured output for classification and field extraction — can obtain or approximate the `Confidence` score this repo's domain model requires (see `CONTEXT.md`'s **Confidence** and **Confidence Threshold** entries, and ADR-0001, "Two-phase classification"). Prior research (`docs/research/json-schema-for-classification-extraction-validation.md`, §3d) already established that JSON Schema itself has no native confidence concept and that any `confidence` field in a tool-use response shape is this repo's own invention. This document does not re-litigate that; it investigates the separate question of how such a value could actually be *derived* from the model, and reports what is and is not confirmed by a primary source for each candidate mechanism.

Every claim below is either (a) a direct quote or close paraphrase from a page fetched during this research, with the URL given, or (b) explicitly marked as **not confirmed by a fetched primary source** where the investigation came up empty. Nothing is asserted from training-data memory alone.

---

## Summary of findings

| Mechanism | Anthropic primary-source support? | Extra model calls |
|---|---|---|
| Token logprobs / token-probability API parameter | **Refuted.** No such parameter exists on the Messages API. | n/a |
| Self-reported confidence field in the tool schema | Not documented as a named pattern; JSON-Schema-constrainable via documented structured-outputs/tool-use mechanics. Anthropic's own docs do *not* state it is well-calibrated. | 0 (rides the same call) |
| Sampling-based self-consistency (Best-of-N) | **Confirmed** — Anthropic documents this as a hallucination-detection and workflow-reliability technique in two separate first-party sources. | ×N |
| Extended/adaptive thinking | Documented as a reasoning-transparency feature; **confirmed absent** any confidence/probability output. | 0 (if already in use) |
| Citations | Documented; **confirmed absent** any relevance/confidence score field. | 0 |

---

## 1. Token logprobs / token-probability signal — refuted

The Messages API reference (`POST /v1/messages`) was fetched in full to enumerate every top-level request parameter. The complete list, as documented: `max_tokens`, `messages`, `model`, `cache_control`, `container`, `inference_geo`, `metadata`, `output_config`, `service_tier`, `stop_sequences`, `stream`, `system`, `temperature`, `thinking`, `tool_choice`, `tools`, `top_k`, `top_p`. [platform.claude.com/docs/en/api/messages](https://platform.claude.com/docs/en/api/messages)

**There is no `logprobs`, `top_logprobs`, or any parameter that returns token-level log probabilities or per-token output probabilities.** This is not an oversight in this research — it is the complete enumerated parameter list from the API reference page itself, and no parameter name resembling a probability/logprob output appears anywhere in it. Unlike OpenAI's Chat Completions API (which does expose `logprobs`/`top_logprobs`), Anthropic's Messages API has never surfaced this per the fetched reference, and nothing in the migration guide, tool-use docs, or structured-outputs docs (also fetched during this research) introduces such a parameter for any current or historical model. **This mechanism is not available on the Anthropic Messages API and cannot be used, for tool use or otherwise.**

As a secondary consequence: because there is no logprob signal, there is also no way to compute a token-level or sequence-level probability for a `tool_use` block's JSON output (e.g. "the model was 92% confident in the `input.documentType` token"). Any confidence number this system produces must come from a mechanism the model is *asked* to produce, not one the API exposes about its own decoding process.

---

## 2. Self-reported certainty via a schema field

### Is this a documented/recommended Anthropic pattern?

**Not as a named, dedicated pattern for confidence scoring.** Three tool-use/structured-output pages were fetched looking specifically for this:

- **Tool use overview** ([platform.claude.com/docs/en/agents-and-tools/tool-use/overview](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)) — describes the tool-call round trip end to end (tool definition → `tool_use` block → `tool_result`) with no mention of confidence, certainty, or calibration anywhere in the fetched content.
- **Define tools** ([platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools)) — the page that documents tool-definition best practices (`name`, `description`, `input_schema`, `input_examples`, and the "best practices for tool definitions" list: detailed descriptions, consolidating related operations, meaningful namespacing, returning only high-signal information). **None of these best practices mention adding a confidence/certainty field to a tool's `input_schema`.** The page also links to Anthropic's engineering post "[Writing tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents)" for deeper tool-design guidance, but nothing in the fetched `define-tools` page itself addresses self-reported confidence.
- **Prompting best practices** ([platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)) — Anthropic's single consolidated prompt-engineering reference (the former separate "increase consistency" and "reduce hallucinations" guides have been folded into this page and the guardrails section covered in §3 below). This page does contain one instance of Claude tracking self-reported confidence, but it is scoped to **agentic research workflows**, not classification/extraction: a sample prompt under "Research and information gathering" reads *"develop several competing hypotheses. Track your confidence levels in your progress notes to improve calibration. Regularly self-critique your approach and plan."* This is guidance for an open-ended research agent maintaining a scratchpad across many tool calls — not a recommendation to emit a numeric `confidence` field in a structured classification/extraction tool's JSON output. **No page fetched during this research describes self-reported confidence as a technique for classification or field-extraction confidence scoring specifically.**

### Is it constrainable via documented mechanics?

Yes — mechanically, nothing prevents it. Anthropic's structured-outputs and strict-tool-use features, which *are* documented (`output_config.format` / `strict: true` on a tool definition, both referenced from the guardrails pages fetched below), let a caller add an arbitrary JSON Schema property to a tool's `input_schema`, including a `confidence` field typed as a number. The **guardrails ("mitigate jailbreaks and prompt injections")** page, fetched during this research, gives worked examples of exactly this general shape — asking Claude to emit a small structured verdict (e.g. `{"is_harmful": boolean}`, `{"injection_suspected": boolean}`) constrained by `output_config.format` with a JSON Schema. [platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/mitigate-jailbreaks](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/mitigate-jailbreaks) These are classification-style verdicts, structurally identical in shape to "emit a `confidence: number` alongside a `documentType: string`" — but note neither of these worked examples is a confidence score; they are boolean classifications. No fetched Anthropic example asks the model for a self-reported probability/confidence number.

### Calibration caveats Anthropic documents

**None found.** This research specifically searched for an explicit Anthropic statement that models are poorly calibrated when self-reporting numeric confidence/probability, on the theory that Anthropic's own hallucination-reduction guidance would be the natural place for such a caveat. It is not there. The "Reduce hallucinations" page (§3 below) recommends *allowing* Claude to express uncertainty in words ("say 'I don't know'") but makes no claim, positive or negative, about the reliability of a numeric confidence score Claude might self-report. **This document cannot confirm from a fetched Anthropic primary source that self-reported numeric confidence is, or is not, well-calibrated.** That caveat is a documented finding in the broader (non-Anthropic, secondary) LLM-calibration literature, not something Anthropic's own docs assert one way or the other — and per this document's citation standard, it is called out here as unconfirmed rather than asserted.

---

## 3. Sampling-based agreement / self-consistency

### Anthropic-specific guidance found

Two first-party sources directly support this mechanism, one framed as a hallucination-detection technique and one as a general workflow pattern:

**"Reduce hallucinations"** ([platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations)), under "Advanced techniques":

> **"Best-of-N verification**: Run Claude through the same prompt multiple times and compare the outputs. Inconsistencies across outputs could indicate hallucinations."

The same page's "Basic hallucination minimization strategies" also documents letting Claude express uncertainty verbally ("Allow Claude to say 'I don't know'") as a distinct, complementary technique — not the same mechanism as Best-of-N, but relevant background: Anthropic's own hallucination guidance treats *inter-sample disagreement*, not a self-reported number, as the trustworthy signal.

**Anthropic's engineering blog, "Building effective agents"** ([anthropic.com/engineering/building-effective-agents](https://www.anthropic.com/engineering/building-effective-agents)) documents the same idea as a named workflow pattern, "parallelization," with a "voting" variant:

> Voting means "running the same task multiple times to get diverse outputs," with examples including "reviewing a piece of code for vulnerabilities, where several different prompts review and flag the code if they find a problem," and "evaluating whether a given piece of content is inappropriate, with multiple prompts evaluating different aspects or **requiring different vote thresholds** to balance false positives and negatives."

This is closer to majority-vote self-consistency as this repo would use it: N independent calls, agreement rate (or vote threshold) as the reliability signal. The same post also documents an "evaluator-optimizer" pattern (one call generates, another critiques in a loop) — a related but distinct verification pattern, recommended "when we have clear evaluation criteria, and when iterative refinement provides measurable value," which is a second-call-per-attempt cost shape, not an N-sample agreement-rate shape.

### Temperature semantics and determinism (does this technique actually work on Claude?)

For sample-based agreement to produce a meaningful signal, repeated calls need to actually vary. Two primary-source facts bear directly on this:

1. **`temperature` documented semantics**, from the Messages API reference: *"Amount of randomness injected into the response. Defaults to `1.0`. Ranges from `0.0` to `1.0`. Use `temperature` closer to `0.0` for analytical / multiple choice, and closer to `1.0` for creative and generative tasks."* And critically: **"Note that even with `temperature` of `0.0`, the results will not be fully deterministic."** [platform.claude.com/docs/en/api/messages](https://platform.claude.com/docs/en/api/messages) — this means repeated identical-parameter calls to Claude are *never* guaranteed to return byte-identical output, at any temperature setting, on any model that accepts the parameter. This is exactly the precondition self-consistency needs (samples that can actually disagree) — but it also means a caller cannot rely on `temperature=0` as a determinism guarantee if the goal were instead to *suppress* variance.
2. **`temperature`/`top_p`/`top_k` are removed entirely on the newest model tier.** The official Migration Guide states, for Claude Opus 4.7 and later (Opus 4.8, Sonnet 5, and Claude Fable 5 by extension per this repo's cached model-migration reference — confirmed directly for Opus 4.7 in the fetched page): *"Setting `temperature`, `top_p`, or `top_k` to any non-default value on Claude Opus 4.7 returns a 400 error. The safest migration path is to omit these parameters entirely from request payloads. Prompting is the recommended way to guide model behavior on Claude Opus 4.7."* [platform.claude.com/docs/en/about-claude/models/migration-guide](https://platform.claude.com/docs/en/about-claude/models/migration-guide) The same page repeats the determinism caveat: *"If you were using `temperature = 0` for determinism, note that it never guaranteed identical outputs on prior models."*

Net effect: on current-generation models, a caller cannot even elevate `temperature` to deliberately increase sample diversity for self-consistency — the parameter is rejected outright at any non-default value. Self-consistency on these models has to rely on the model's own non-zero baseline stochasticity (point 1) rather than a tunable temperature knob. On older models where `temperature` is still accepted, it remains available as a lever, but Anthropic's own docs do not claim a specific temperature value optimizes self-consistency signal quality — no such guidance was found.

### Cost/latency shape

Both documented sources describe this mechanism as literally re-running the same call N times — an unambiguous ×N multiplier on model calls (and correspondingly ×N latency if run sequentially, or ×N cost with parallel fan-out). Neither source suggests a cheaper partial-sampling variant (e.g. reusing thinking tokens across samples, or a native "N-best" style parameter) — no such API feature exists per the enumerated parameter list in §1.

---

## 4. Other candidate mechanisms surfaced by Anthropic's own docs

### Extended / adaptive thinking

The extended-thinking page was fetched specifically to check whether thinking output could serve as a confidence proxy. **Confirmed absent:** the page describes thinking blocks purely as reasoning transparency — *"When extended thinking is turned on, Claude creates `thinking` content blocks where it outputs its internal reasoning. Claude incorporates insights from this reasoning before crafting a final response."* [platform.claude.com/docs/en/build-with-claude/extended-thinking](https://platform.claude.com/docs/en/build-with-claude/extended-thinking) Nothing in the fetched page describes thinking blocks as carrying, or being usable to derive, a confidence or probability score, and nothing describes running multiple thinking passes for agreement-based confidence — that would just be Best-of-N (§3) with thinking enabled on each sample, not a distinct mechanism.

### Citations

The citations feature was fetched to check for a relevance/confidence score attached to each citation. **Confirmed absent:** the documented citation shape is `cited_text`, `document_index`, `document_title`, and a location object (`char_location`, `page_location`, or `content_block_location` depending on source type) — see [platform.claude.com/docs/en/build-with-claude/citations](https://platform.claude.com/docs/en/build-with-claude/citations) and the cross-referencing entry in this skill's own claude-api reference. No score, weight, or confidence field is part of the documented citation object. Citations could plausibly serve a *different* trust purpose in this system — e.g. letting a caller verify an extracted field's value against the exact source text/page it was pulled from — but that is source-grounding, not a numeric Confidence in the [0,1] sense CONTEXT.md defines. **Citations are not usable as a source for the Confidence score itself.**

### Structured outputs / strict tool use as an enabling (not scoring) mechanism

Both `output_config.format` (JSON-schema-constrained text output) and `strict: true` (schema-conformant tool calls) are documented, real API features that *guarantee* a `confidence` field — once you decide to ask for one — will parse as the declared type (e.g. `number`). They do not supply the value; they only guarantee its shape. This confirms the mechanical feasibility noted in §2 but adds nothing about calibration.

---

## Recommendation

Given the two call sites in this system's domain model and their existing call budgets:

- **Classification** is already **two** model calls per Document under ADR-0001 (page-level, then document-level) — ADR-0001's own stated rationale for the second call is explicitly to avoid "masking real classification disagreement behind a silent tiebreak," i.e., ADR-0001 already treats extra model calls as a cost to be spent only when it buys something a cheaper mechanism can't.
- **Extraction** is **one** model call per Document.

Against that backdrop, and given the findings above:

1. **Use self-reported confidence via a schema field as the primary mechanism, for both Classification and Extraction.** This is the only mechanism investigated that adds **zero** extra model calls — it rides the same document-level Classification call and the same Extraction call that already have to happen. Concretely: add a `confidence` property (type `number`, and ideally `minimum: 0` / `maximum: 1` per the JSON Schema constraints already catalogued in `docs/research/json-schema-for-classification-extraction-validation.md`) to the document-level classification tool's `input_schema`, and to each extracted field's representation in the extraction tool's `input_schema`. This is not a pattern Anthropic documents by name for this purpose (§2) — it is this repo's own invention, exactly as the prior JSON Schema research already flagged — but it is mechanically sound (structured outputs / strict tool use guarantee the shape) and costs nothing beyond prompt-token overhead for the extra field(s).
2. **Do not adopt blanket N-sample self-consistency (Best-of-N / voting) as the primary mechanism.** It is the one mechanism Anthropic documents in first-party sources as a real reliability technique (§3), but its cost shape is a flat ×N multiplier on model calls — directly contrary to ADR-0001's explicit goal of minimizing extra model calls, and it would apply that multiplier to *every* Document's Classification and Extraction, not just the uncertain ones.
3. **Where higher assurance than a bare self-reported number is wanted, spend the extra calls selectively, not universally.** Because no fetched source confirms self-reported confidence is well-calibrated (§2), and because ADR-0001 has already established a precedent in this codebase for spending exactly one extra call to resolve disagreement rather than trusting a single pass, the same shape applies naturally here: reserve Best-of-N (Anthropic's own documented technique, §3) for the narrow band of Documents whose self-reported confidence lands close to the matched Schema's Confidence Threshold — i.e., use the cheap self-reported number as a first-pass filter, and only pay for N-sample agreement on the cases where the cheap number is itself ambiguous. This keeps the added-call cost proportional to genuine uncertainty rather than applying it uniformly, consistent with the cost-consciousness ADR-0001 already establishes for this pipeline. This is an architectural suggestion for the driving session to evaluate and formalize (e.g. as its own ADR) — it is not itself confirmed by any Anthropic documentation as a recommended hybrid, since Anthropic's sources describe self-reported confidence and Best-of-N as separate, independent techniques, never combined as an escalation ladder.
4. **Do not rely on temperature tuning as part of any self-consistency design.** On current-generation models (Opus 4.7 and later), `temperature`/`top_p`/`top_k` are rejected outright at non-default values (§3), so sample diversity has to come from the model's own baseline non-determinism — which Anthropic's own docs confirm exists even at `temperature: 0.0` — not from a tunable knob.
5. **Token logprobs, extended thinking, and citations are ruled out** as direct sources for the Confidence score (§1, §4) — none of them expose a probability or confidence signal per the fetched API surface.

Whatever mechanism is chosen, because no Anthropic primary source confirms self-reported confidence is calibrated, this system's own empirical validation (comparing self-reported Confidence against ground-truth correctness on a labeled holdout set, per Document Type) is necessary before trusting the Confidence Threshold gate — that validation work is outside this research's scope but should be tracked as a follow-up before this mechanism ships.
