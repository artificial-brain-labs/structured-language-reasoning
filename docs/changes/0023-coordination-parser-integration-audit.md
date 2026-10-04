# Change 0023 — Coordination Parser Integration Audit

## Purpose

The declarative noun-phrase coordination foundation introduced in Change 0022 was structurally present in the grammar, but its parser integration did not consistently expose coordinated role members to the semantic layer.

This change closes that integration gap without adding sentence-specific parsing logic.

## Changes

### 1. Role-aware coordination extraction

`src/parser.py` now inspects the declarative roles of the selected statement production and checks each role's child for coordination metadata.

This is independent of whether coordination occurs in the subject or object position.

Examples:

- `cat and dog eat rat`
- `cat eats rat and mouse`
- `cat and dog eat rat and mouse`

The parser exposes coordinated members through `subject_words`, `object_words`, and corresponding surface-word tuples.

### 2. Recursive coordination structure

`src/compositional_parser.py` now recursively expands nested coordination metadata.

Nested coordination remains structurally representable through recursive grammar composition. When multiple derivations are possible, the parser returns `AMBIGUOUS` rather than selecting an association implicitly. This preserves the no-guessing rule.

### 3. Semantic Cartesian expansion

The existing semantic composition model already expands coordinated subjects and objects compositionally. Regression coverage now verifies that both sides produce the Cartesian operation set.

For two subjects and two objects, four operations are expected.

### 4. Coverage contract correction

Coordination is marked `PARTIAL` in `knowledge/grammar_coverage.json`.

Only coordinated noun phrases are currently implemented. Coordinated statements and coordinated adjectives remain planned. The coverage status therefore now reflects implementation rather than declaring the whole coordination family complete.

### 5. Regression-test hygiene

`tests/test_reference_evidence.py` now explicitly imports `pytest`, required by its declarative reference-policy validation test.

## Architectural constraints preserved

- Grammar remains authoritative data.
- Python contains generic parsing/composition mechanisms only.
- No conjunction-specific execution logic was added.
- No sentence-specific exceptions were introduced.
- Coordination remains a syntactic/semantic composition feature; it does not become a reasoning heuristic.
- Unknown and ambiguous states remain governed by the existing parser and semantic layers.

## Validation

Added regression coverage for:

1. coordinated object parsing;
2. coordinated subject parsing;
3. recursive coordination ambiguity detection;
4. subject/object Cartesian expansion.

The repository runtime test suite should be run from the `v1.0-development` checkout after pulling these commits.
