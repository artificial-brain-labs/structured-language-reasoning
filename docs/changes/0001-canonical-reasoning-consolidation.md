# Change 0001 — Canonical Reasoning Consolidation

## Status

Implemented — validation pending local test execution

## Date

2026-09-22

## Change Type

Architecture / Reasoning / Provenance

## Problem

SLRM has established `SemanticGraphReasoner` as the canonical reasoning mechanism, but parts of the query and explanation layer still reconstruct reasoning independently.

In particular, `GraphQuery.explain_classification()` can independently walk ontology parent relationships to construct an explanation path instead of consuming the derived edges produced by the canonical graph reasoner.

This creates two risks:

1. The system can contain two implementations of the same reasoning semantics.
2. Query results and explanations can diverge from the actual canonical derived graph.

## Existing Architecture

The intended V1.x flow is:

```text
Asserted User Knowledge
        ↓
   Semantic Graph
        ↓
SemanticGraphReasoner
        ↓
   Derived Graph
```

The semantic graph is a projection of user memory and derived results. The graph reasoner is the authoritative mechanism for ontology and configured inference.

Legacy reasoning APIs may remain for compatibility, but they must delegate to the canonical mechanism.

## Decision

Consolidate reasoning so that the canonical graph reasoner is the single authoritative source for derived knowledge.

Query and explanation components must consume the asserted/derived graph produced by the canonical reasoning pipeline rather than independently re-implementing ontology traversal or inference.

Target architecture:

```text
                 ┌── Query
                 │
Asserted Graph → Graph Reasoner → Derived Graph
                                      │
                                      └── Explanation
```

The explanation layer may format or trace canonical derivations, but must not independently create a competing derivation.

## Rationale

A reasoning result should have one authoritative derivation.

This supports:

- consistent query and explanation behavior;
- reliable provenance;
- easier auditing;
- fewer duplicated reasoning rules;
- future extension of inference without modifying multiple consumers;
- the project's no-guessing and data-driven architecture principles.

## Alternatives Considered

### Keep independent explanation logic

Rejected because it duplicates ontology reasoning and can diverge from the canonical derived graph.

### Move all reasoning into QueryEngine

Rejected because reasoning is a system-level semantic capability and should not be owned by a query consumer.

### Maintain multiple equivalent reasoning implementations

Rejected because equivalent implementations create long-term semantic drift and make provenance harder to audit.

## Architectural Impact

Expected affected components:

- `src/graph_reasoner.py`
- `src/graph_query.py`
- `src/main.py`
- reasoning/provenance tests
- architecture documentation

No new reasoning component should be introduced unless the existing canonical graph representation cannot express the required derivation.

## Invariants

After implementation:

1. `SemanticGraphReasoner` remains the authoritative V1.x graph reasoning mechanism.
2. Query results must be based on canonical asserted/derived graph state.
3. Ontology derivations must form their proof chain in the canonical derived graph.
4. Explanations must trace canonical derived evidence.
5. Derived knowledge must remain distinct from asserted knowledge.
6. Derived edges must retain provenance/support.
7. No guessing or implicit assertion promotion may be introduced.
8. Legacy reasoning APIs must not create a competing reasoning source of truth.

## Implementation

Implemented the first consolidation pass:

- `SemanticGraphReasoner` now emits ontology inheritance as a canonical chain of derived graph edges (`CAT -> FELINE -> MAMMAL -> ANIMAL`) rather than unrelated direct ancestor edges from the original entity.
- Each derived step retains support pointing to the original asserted graph evidence.
- `SemanticGraphQuery.explain_classification()` now traverses and formats those actual canonical graph edges instead of independently walking `Ontology.parent()`.
- Added regression coverage proving the canonical derived chain and that explanation steps correspond to graph edges.

## Implementation Plan

1. Inspect the current canonical derived-edge representation and proof requirements.
2. Refactor explanation to consume canonical derived edges.
3. Preserve explainable proof output and existing semantics.
4. Add regression tests proving explanation evidence matches canonical derived graph edges.
5. Run the complete test suite.
6. Record final implementation and validation details in this document.

## Testing Plan

Tests must cover:

- ontology-derived classification;
- canonical derived-edge provenance;
- explanation-to-derived-edge consistency;
- transitive configured inference;
- unknown entities;
- legacy compatibility facade behavior;
- preservation of asserted versus derived epistemic state.

## Validation

Repository-level test execution could not be run from the available environment because the Codespace repository is not mounted in the current runtime. The changes therefore remain **validation pending** until `pytest -q` is run in the project Codespace.

Expected relevant commits:

- `f11dc89` — canonical ontology proof chain
- `a22e837` — explanation consumes canonical graph edges
- `bc552bd` — canonical reasoning regression tests

## Future Considerations

The canonical reasoner now represents ontology inheritance as a multi-step graph chain so proof structure is itself canonical. A future change should preserve this property. Alternative provenance paths should remain representable when multiple independent derivations support the same graph fact.

Alternative provenance paths should also remain representable when multiple independent derivations support the same graph fact.

## Historical Note

This change document establishes the project convention that meaningful architecture and behavior changes are documented alongside implementation. Future developers should consult `docs/changes/` before changing related architecture and should use these records as historical design context.
