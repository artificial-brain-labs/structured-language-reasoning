# Conflict-Aware Canonical Reasoning

## Problem

Conflicting user evidence must not participate in semantic derivation. At the same time, an unrelated valid fact must remain available for reasoning.

## Existing architecture

V1.x uses `SemanticGraph` as the canonical graph representation and `SemanticGraphReasoner` as the canonical reasoning mechanism. User-memory conflicts are projected into graph edges with `status="CONFLICTED"`.

## Decision

Canonical reasoning consumes only asserted evidence.

The reasoner therefore derives from `graph.asserted_edges()`, while conflicted edges remain visible for provenance and inspection but cannot become reasoning premises.

This gives the following invariant:

```
ASSERTED + contradictory evidence
        ↓
     CONFLICTED
        ↓
not a reasoning premise
```

Unrelated asserted evidence continues to participate normally.

## Rationale

This is the V1.x equivalent of invalidating descendants of an unsupported reasoning premise, without introducing a second operator-based backtracking kernel. It preserves the canonical SemanticGraph/SemanticGraphReasoner architecture and avoids competing sources of truth.

## Implementation

The existing canonical reasoner already filters premises through `asserted_edges()`. Regression tests now explicitly verify:

1. a conflicted taxonomic premise produces no derived ancestors;
2. an unrelated asserted premise still produces valid derivations;
3. reasoning does not mutate the asserted graph.

## Architectural invariants

- Conflicted evidence is never treated as asserted evidence.
- Unknown remains distinct from false.
- Derived knowledge remains transient and non-persistent.
- Unrelated valid evidence is not discarded because another fact is conflicted.
- SemanticGraph remains the canonical graph representation.
- SemanticGraphReasoner remains the canonical reasoning mechanism.

## Validation

The regression tests are implemented in `tests/test_graph_reasoner.py`.

## Future considerations

If future reasoning operators introduce multi-step dependency graphs beyond the current canonical graph reasoner, invalidation should continue to operate on dependency provenance rather than introducing an independent reasoning state or competing graph.
