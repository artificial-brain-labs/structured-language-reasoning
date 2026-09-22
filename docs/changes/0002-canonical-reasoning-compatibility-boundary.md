# Change 0002 — Canonical Reasoning Compatibility Boundary

## Status
Implementation in progress

## Date
2026-09-22

## Change Type
Architecture / Reasoning / Compatibility / Provenance

## Problem
Change 0001 established SemanticGraphReasoner as the authoritative reasoning kernel and changed ontology inheritance into a canonical proof chain: CAT -> FELINE -> MAMMAL -> ANIMAL.
The synchronized test suite exposed compatibility regressions because legacy reasoning APIs and some consumers still assumed the earlier direct-ancestor projection. Identity explanations also exposed an entity-node representation problem: an entity such as Tom has concept UNKNOWN, but its display name must remain Tom rather than rendering UNKNOWN.

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

## Rationale
The compatibility boundary allows existing callers to continue receiving stable semantic results while preserving a single reasoning implementation.
Reintroducing direct ancestor edges solely for legacy consumers would create two competing representations of the same inference and weaken provenance auditing.
Display-name handling is likewise presentation/identity mapping, not reasoning.

## Required Invariants
- No derived fact becomes asserted user memory.
- Canonical ontology derivations remain DERIVED and ONTOLOGY sourced.
- Every derived step retains provenance support to asserted evidence.
- Compatibility APIs do not create independent inference.
- Entity names are preserved across identity proof traversal.
- Unknown concepts remain unknown; no name-based type inference is introduced.
- Graph-local adapter IDs do not replace memory-level entity identity.
- Canonical proof chains remain traversable by query and explanation layers.

## Implementation Plan
1. Inspect legacy Reasoner return expectations and canonical graph identity boundaries.
2. Adapt compatibility projections to traverse canonical derivations from an entity's asserted classification.
3. Preserve compatibility behavior for direct class-handle queries using the existing temporary compatibility seed.
4. Correct identity-proof display to use entity names where appropriate.
5. Migrate obsolete tests from direct-ancestor expectations to canonical proof-chain expectations where the architecture has intentionally changed.
6. Preserve the unknown-subject graph boundary and compatibility behavior for manually inserted unknown subjects.
7. Run the complete test suite.
8. Update this document with final validation and commit references.

## Testing Plan
Cover entity classification compatibility, class-handle compatibility, the canonical CAT -> FELINE -> MAMMAL -> ANIMAL chain, provenance and non-persistence of derived knowledge, identity explanation using entity names, unknown graph subjects, legacy derive() output, and asserted versus derived separation.

## Validation

Implementation is complete. Full pytest -q execution is pending in the project Codespace.

The implementation:
- projects canonical ontology derivations through the legacy Reasoner compatibility surface;
- preserves canonical derived edges and provenance;
- maps graph-local unknown-subject IDs back to their legacy subject representation;
- preserves entity display names in identity/classification explanations;
- updates graph tests to validate the canonical CAT -> FELINE -> MAMMAL -> ANIMAL chain rather than requiring obsolete direct Tom -> ANIMAL edges.


## Relationship to Change 0001
Change 0001 defines the canonical reasoning representation.
Change 0002 defines how legacy compatibility surfaces consume that representation without becoming a second reasoning source.

## Future Considerations
If legacy compatibility APIs are eventually removed, this boundary can be simplified. Until then, compatibility translation should remain thin and should never acquire independent reasoning rules.