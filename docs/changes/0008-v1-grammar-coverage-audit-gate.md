# Change 0008 — V1 Grammar Coverage Audit Gate

## Summary

The V1 grammar foundation is now linked explicitly to the declarative grammar through a machine-readable production map.

## Changes

- Added `production_map` to `knowledge/grammar_coverage.json`.
- Linked every required V1 construction to one or more productions in `knowledge/grammar_foundation.json`.
- Added `tests/test_grammar_coverage.py` to verify that every required construction has a declared production mapping and that every mapped production exists.
- Expanded `tests/test_grammar_foundation_v1.py` with semantic regression coverage for:
  - transitive relations
  - state assignment
  - classification
  - identity
  - property assignment
- Replaced the linguistically awkward `The Tom eats the mouse` regression example with `The dom eats the mouse`.

## Architectural significance

This makes the grammar coverage contract executable at the architecture level.

The implementation now has three distinct layers:

1. **Coverage contract** — declares what SLR V1 claims to support.
2. **Grammar foundation** — declares how those constructions are parsed.
3. **Regression/compliance tests** — verify that declared coverage remains connected to implemented grammar.

The test does not encode sentence-specific linguistic logic. It validates the declarative relationship between the coverage specification and grammar data.

## Scope

This change does not add new reasoning operators, reasoning heuristics, or sentence-specific parser exceptions.

It also does not claim complete natural-English coverage. V1 remains complete only within the explicitly declared SLR English subset.

## Verification

The coverage-to-production linkage was checked while applying the change. The repository test suite was not executed in this environment, so runtime test success is not claimed.
