# Change 0015 — Declarative Reference Policy Contract

## Purpose

Contextual reference resolution now has an explicit declarative contract. Lexical reference metadata is validated when the lexicon is loaded rather than being accepted as unconstrained runtime data.

## Changes

- Added `knowledge/reference_policy.json`.
- Added `src/reference_policy.py`.
- `Lexicon` validates pronoun reference metadata at initialization.
- Contextual references must declare the required policy fields.
- Allowed roles and evidence kinds are defined by data, not Python-specific pronoun logic.
- A pronoun cannot simultaneously declare an anchor reference and a contextual reference.
- Pronouns without either reference form are rejected.

## Contract

The current V1 contract defines:

- `CONTEXTUAL` references
  - required policy: `allowed_roles`, `required_evidence`
  - supported roles: `subject`, `object`
  - supported evidence: `PRIOR_MENTION`, `ROLE`
- anchor references remain represented by the existing `referent` declaration.

## Architectural significance

This strengthens the data-before-logic boundary:

```
Lexicon → Reference Policy Contract → Reference Resolver
```

The resolver is not allowed to silently invent unsupported reference modes or evidence semantics.

This is a validation boundary, not a reasoning heuristic. It does not add salience, scoring, agreement inference, probability, or automatic antecedent selection.

## Scope boundary

This change does not implement:

- gender or number agreement
- recency-based selection
- salience ranking
- probabilistic anaphora
- descriptive noun-phrase reference
- discourse inference

Ambiguous contextual references remain ambiguous until declaratively supported evidence produces a unique candidate.

## Verification

Added `tests/test_reference_policy.py` covering:

1. acceptance of current reference metadata
2. required policy fields
3. unsupported evidence rejection
4. mixed reference declaration rejection
5. missing reference metadata rejection
