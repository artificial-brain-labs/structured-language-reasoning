# Change 0004 — Generic Identity-Aware Relation Queries and Reasoning Subject Preservation

## Status

Implemented on `v1.0-development`.

## Problem

Two regressions exposed architectural boundary issues:

1. Ontology inheritance derivation used the current concept node as the subject of each derived edge, rather than preserving the original asserted entity.
2. Relation queries canonicalized identities inside `QueryEngine`, making identity resolution a query-handler concern rather than a generic graph traversal capability.

## Decision

### Reasoning

Ontology inheritance preserves the original asserted subject across every derived taxonomic edge.

For:

`Tom IS_A CAT`

and ontology:

`CAT IS_A FELINE IS_A MAMMAL`

the derived relations remain attached to `Tom`:

`Tom IS_A FELINE`
`Tom IS_A MAMMAL`

The derivation support continues to reference the original asserted evidence.

### Query traversal

Identity resolution is handled by `SemanticGraphQuery` as a generic graph capability.

Relation queries traverse explicit identity paths before evaluating the requested predicate. This applies generically to object and subject queries and does not encode particular words, entities, or sentence forms.

`Dom SAME_AS Tom`
`Tom EATS Rat`

therefore permits:

`objects(Dom, EATS) -> Rat`

without requiring `QueryEngine` to special-case identity.

## Invariants preserved

- No hard-coded entity or sentence knowledge.
- Data-before-logic.
- Explicit identity only.
- Conflicted edges remain excluded.
- Derived knowledge remains non-asserted.
- Semantic graph remains the canonical reasoning representation.
- Query traversal remains read-only.

## Regression coverage

Added tests for:

- preservation of the original reasoning subject during ontology derivation;
- generic object-query grammar;
- identity-aware relation querying.
