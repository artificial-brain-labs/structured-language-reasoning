# Change 0004 — Generic Identity-Aware Relation Queries and Canonical Ontology Proof Chains

## Status

Implemented on `v1.0-development`.

## Problem

Two regressions exposed architectural boundary issues:

1. Ontology inheritance needed to remain a canonical concept-to-concept proof chain rather than producing redundant entity-to-ancestor edges.
2. Relation queries canonicalized identities inside `QueryEngine`, making identity resolution a query-handler concern rather than a generic graph traversal capability.

## Decision

### Canonical ontology reasoning

For an asserted classification:

`Tom IS_A CAT`

and ontology:

`CAT IS_A FELINE IS_A MAMMAL IS_A ANIMAL`

the semantic graph contains the asserted edge:

`Tom -> CAT`

followed by derived ontology edges:

`CAT -> FELINE -> MAMMAL -> ANIMAL`

Each derived edge points to the immediately following ontology concept. Its support references the original asserted evidence. This preserves a transparent proof chain and avoids materializing redundant direct classifications such as `Tom IS_A ANIMAL`.

The canonical graph therefore distinguishes:

- user evidence: entity -> asserted concept
- ontology reasoning: concept -> parent concept
- query explanation: traversal across both layers

This is the representation used by the canonical graph reasoner and proof engine.

### Query traversal

Identity resolution is handled by `SemanticGraphQuery` as a generic graph capability.

Relation queries traverse explicit identity and taxonomic classification paths before evaluating the requested predicate. This allows a relation asserted on a concept to be queried through an explicitly classified entity, without encoding particular words, entities, or sentence forms.

`Dom SAME_AS Tom`  
`Tom EATS Rat`

therefore permits:

`objects(Dom, EATS) -> Rat`

Likewise, when `Tom IS_A CAT` and `CAT EATS Rat` are explicit graph facts:

`objects(Tom, EATS) -> Rat`

without requiring `QueryEngine` to special-case identity.

## Invariants preserved

- No hard-coded entity or sentence knowledge.
- Data-before-logic.
- Explicit identity only.
- Conflicted edges remain excluded.
- Derived knowledge remains non-asserted.
- Semantic graph remains the canonical reasoning representation.
- Query traversal remains read-only.
- Proof paths remain composed from actual graph edges.

## Regression coverage

Added or corrected tests for:

- canonical ontology concept-chain derivation;
- generic object-query grammar;
- identity-aware relation querying;
- proof-chain provenance and asserted-versus-derived status.
