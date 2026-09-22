# Change 0002 — Canonical Reasoning Compatibility Boundary

## Status
Implemented — validation passed

## Date
2026-09-22

## Change Type
Architecture / Reasoning / Compatibility / Provenance

## Problem
Change 0001 established SemanticGraphReasoner as the authoritative reasoning kernel and changed ontology inheritance into a canonical proof chain: CAT -> FELINE -> MAMMAL -> ANIMAL.
The synchronized test suite exposed compatibility regressions because legacy reasoning APIs and some consumers still assumed the earlier direct-ancestor projection. Identity explanations also exposed an entity-node representation problem: an entity such as Tom has concept UNKNOWN, but its display name must remain Tom rather than rendering UNKNOWN.

After the first Change 0002 implementation, the complete suite reached 243 passing tests with two remaining failures:
1. The canonical explanation regression test compared human-readable proof labels directly with graph node IDs.
2. The legacy Reasoner.derive() projection returned ontology class concepts where the legacy API requires the underlying memory entity IDs for explicitly represented class entities.

These were compatibility-boundary representation defects, not reasons to change the canonical reasoning model.

## Existing Architecture
Canonical reasoning is:

Asserted Knowledge -> Semantic Graph -> SemanticGraphReasoner -> Canonical Derived Graph -> Query / Explanation

The canonical graph distinguishes entity identity/node ID, entity display name, entity concept, ontology class nodes, asserted edges, derived edges, and provenance/support.
Legacy Reasoner APIs remain part of the public compatibility surface.

## Decision
Preserve the canonical graph representation and adapt compatibility consumers to it.
1. SemanticGraphReasoner remains the only authoritative derivation mechanism.
2. Reasoner.infer_is_a() and Reasoner.derive() are compatibility projections over canonical graph reasoning; they must not independently reason.
3. Compatibility projections may translate canonical class-chain results into the legacy return shape without persisting derived knowledge.
4. Graph-local IDs such as entity:<value> must not leak into legacy semantic identity when a memory entity identity is available.
5. Entity explanations must display node names for entity nodes and concepts for ontology class nodes. UNKNOWN is an internal concept state, not a user-facing identity label.
6. Canonical derived graph edges remain the source of truth for proof paths and provenance.
7. Tests whose expectations require the obsolete direct Tom -> ANIMAL derived edge must be migrated to assert the canonical chain rather than reintroducing duplicate direct derivations.
8. Unknown raw subjects remain representable in the graph without inventing their identity or concept.
9. Explanation validation must compare proof labels through the graph's node-label representation rather than treating display labels as graph IDs.
10. Reasoner.derive() must preserve legacy entity IDs for graph nodes that correspond to memory entities, including class entities such as the explicit MAMMAL and ANIMAL entities used by legacy callers.

## Rationale
The compatibility boundary allows existing callers to continue receiving stable semantic results while preserving a single reasoning implementation.
Reintroducing direct ancestor edges solely for legacy consumers would create two competing representations of the same inference and weaken provenance auditing.
Display-name handling is likewise presentation/identity mapping, not reasoning.
The final two fixes keep representation translation at the compatibility boundary rather than altering canonical graph semantics.

## Required Invariants
- No derived fact becomes asserted user memory.
- Canonical ontology derivations remain DERIVED and ONTOLOGY sourced.
- Every derived step retains provenance support to asserted evidence.
- Compatibility APIs do not create independent inference.
- Entity names are preserved across identity proof traversal.
- Unknown concepts remain unknown; no name-based type inference is introduced.
- Graph-local adapter IDs do not replace memory-level entity identity.
- Canonical proof chains remain traversable by query and explanation layers.
- Explanation labels are presentation values and are never mistaken for canonical graph IDs.
- Legacy derive() preserves memory entity IDs when the graph node originated from a memory entity.

## Implementation
Implemented the compatibility boundary as a projection over canonical graph reasoning:

- Legacy `Reasoner.infer_is_a()` projects canonical ontology derivations without performing independent inference.
- Legacy `Reasoner.derive()` projects canonical derived edges back into the legacy representation.
- Graph-local unknown-subject IDs are translated back to legacy subject representation.
- Memory entity IDs are preserved when canonical graph objects correspond to memory entities.
- Explanation rendering preserves entity names instead of exposing UNKNOWN as an identity label.
- Explanation regression validation compares graph-edge labels through the graph's canonical node-label mapping.
- The canonical graph reasoner remains the sole source of derivation.

## Testing
The final Codespace validation covers:

- entity classification compatibility;
- class-handle compatibility;
- canonical CAT -> FELINE -> MAMMAL -> ANIMAL reasoning;
- provenance and non-persistence of derived knowledge;
- identity explanation using entity names;
- unknown graph subjects;
- legacy derive() output;
- asserted versus derived separation.

## Validation
Validated in the project Codespace on 2026-09-22:

```
pytest -q
245 passed
```

Final result: **245 passed, 0 failed**.

## Relationship to Change 0001
Change 0001 defines the canonical reasoning representation.
Change 0002 defines how legacy compatibility surfaces consume that representation without becoming a second reasoning source.

## Future Considerations
If legacy compatibility APIs are eventually removed, this boundary can be simplified. Until then, compatibility translation should remain thin and should never acquire independent reasoning rules.
