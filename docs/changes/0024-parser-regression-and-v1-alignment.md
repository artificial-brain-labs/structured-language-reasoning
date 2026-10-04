# Parser Regression Repair and V1 Grammar Alignment

## Purpose

This change follows the full-suite regression observed after the declarative coordination work.

## Changes

- Preserve an explicit `UNPARSED` `ParsedSentence` result when the authoritative grammar produces no derivation.
- Do not revive the deleted legacy `knowledge/grammar.json` fallback.
- Declare standalone noun-phrase parsing through grammar data using `default_start_symbols`.
- Remove the duplicate pronoun-specific transitive production because the generic `NP + VERB + NP` production already accepts pronoun NPs; retaining both created artificial ambiguity for inputs such as `I eat mouse`.
- Guard the main processing pipeline so an unparsed interaction reaches the parse-failure response instead of dereferencing a null parse.
- Stop recording the final contextual mention twice after successful execution.
- Render declarative conflict responses before generic success responses so conflicted memories are observable as conflicts.

## Architectural constraints

The repair remains data-driven. The parser does not restore sentence-specific fallback rules or infer unsupported grammar. Ambiguity remains explicit, and unsupported input remains `UNPARSED`.

## Validation

The coordination-focused suite had reached 4 passing tests before this repair. The full-suite output that motivated this change showed 29 failures and 290 passes, with several failures cascading from parser results being `None`. A fresh full-suite run is required after this change; no pass result is claimed here.
