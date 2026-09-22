# SLRM Architecture Principles

## Status

This document defines the architectural invariants that must remain true as Structured Language Reasoning Model (SLRM) evolves.

The principles are stronger than feature requirements. A feature is not considered architecturally complete if it violates one of these invariants.

## 1. No Guessing

SLRM must not convert missing information into an asserted fact.

- Unknown remains unknown.
- An unresolved entity may exist with `UNKNOWN` concept.
- A relation may preserve an explicitly observed unknown object when the relation policy allows it.
- Clarification is preferred when required information cannot be established.

## 2. Unknown Is Not False

The absence of knowledge must never be interpreted as a negative fact.

`UNKNOWN`, `FALSE`, and an explicit negation such as `NOT_EATS` are distinct states.

## 3. Data Before Logic

Knowledge belongs in data structures and knowledge files wherever practical:

- lexicon
- grammar
- ontology
- relations
- inference rules
- execution policies
- operation definitions
- response templates
- clarification policies

Procedural code provides mechanisms for interpreting and validating those declarations. Adding a normal linguistic or world-knowledge concept should not require adding a word-specific Python branch.

Relation roles are the mechanism-level interface for semantic reasoning. Code must resolve roles such as `canonical_taxonomic` from relation data rather than embedding a domain predicate as a reasoning rule.

## 4. User Knowledge Belongs to User Memory

Facts explicitly supplied or explicitly confirmed by a user are stored in that user's memory.

User-specific knowledge must not mutate global/system knowledge.

Separate `SLR` instances must not leak user facts into one another.

## 5. Derived Knowledge Is Not Asserted Knowledge

Inference may produce derived results, but derived results must not automatically become asserted user memories.

For example:

`Tom IS_A CAT`

may derive:

`Tom IS_A FELINE`
`Tom IS_A MAMMAL`
`Tom IS_A ANIMAL`

without storing those derived relations as asserted memories.

## 6. Explicit Classification Is Evidence

An entity's cached base concept must not be silently rewritten merely because an explicit classification was supplied.

`Tom IS_A CAT` is represented as explicit `IS_A` evidence. This preserves the distinction between entity identity, asserted knowledge, and derived knowledge.

## 7. Ontology Provides Inheritance

Shared properties and taxonomic relationships belong to ontology data. Child classes inherit through ontology relationships rather than requiring duplicated procedural rules.

## 8. The Semantic Graph Is a Projection

The semantic graph is a read/query representation of user memory plus derived results. It must not become a second source of truth or invent knowledge.

Graph edges representing user memory retain provenance metadata linking them to the user's evidence ledger when that ledger is available.

## 9. Reasoning Must Be Explainable

Where a conclusion is derived, the system should be able to identify the supporting path or rule rather than presenting an unexplained result.

## 10. Clarification Must Preserve Identity and Context

When clarification is requested, the pending entity and original operation/context must be preserved. A clarification response must bind information to the existing entity rather than creating a replacement entity through a fresh resolution path.

## 11. Epistemic State Must Remain Explicit

SLRM distinguishes the lifecycle of information:

`OBSERVATION -> INTERPRETATION -> ASSERTION -> DERIVATION / HYPOTHESIS`

These states are not interchangeable.

- `OBSERVATION` records what was encountered or communicated.
- `INTERPRETATION` records a structured interpretation without asserting truth.
- `ASSERTION` represents explicitly supplied or explicitly confirmed user knowledge.
- `DERIVATION` represents a conclusion produced by reasoning and is never automatically asserted.
- `HYPOTHESIS` represents a candidate explanation or possibility and is never a fact merely because it is plausible.

The epistemic evidence ledger must preserve provenance and support without treating evidence itself as truth.

## 12. Explicit Confirmation Is Required for Assertion

An `ASSERTION` evidence record requires explicit confirmation. SLRM must not promote an observation, interpretation, derivation, or hypothesis to assertion implicitly.

In particular:

`UNKNOWN != FALSE`

`UNKNOWN != TRUE`

`UNKNOWN != GUESSED`

`DERIVED != ASSERTED`

`HYPOTHESIS != FACT`

## 13. Transient Communication Memory (TCM)

TCM is implemented as a bounded temporary communication store. Its responsibility is raw interaction/conversation material for the active cognitive pipeline; it does not represent identity, asserted knowledge, or enduring user memory.

Persistent user memory contains cognitive transformations such as explicit facts, classifications, relationships, and identity statements. TCM may decay or be cleared independently of user memory.

TCM records do not become assertions merely because they were received. Promotion into user memory occurs through the governed semantic interpretation and execution path.

## 14. Single Cognitive Graph and Reasoning Kernel

`SemanticGraph` is the canonical graph representation and `SemanticGraphReasoner` is the canonical graph reasoning mechanism for the V1.x architecture.

Legacy graph/inference modules, where retained for compatibility, must be facades over the canonical implementation and must not maintain an independent source of truth or competing reasoning rules.

## 15. Evidence-to-Graph Traceability

Every asserted user-memory edge projected into the semantic graph should be traceable to the corresponding evidence record when user evidence is available. Derived edges must identify their supporting graph evidence and derivation mechanism.

## 16. Change Documentation and Historical Traceability

Every meaningful architecture, behavior, semantic, reasoning, memory, governance, knowledge-representation, or externally observable system change must have a corresponding change document under `docs/changes/`.

A change document must record, as applicable:

- problem;
- existing architecture;
- decision;
- rationale;
- alternatives considered;
- architectural impact;
- implementation;
- invariants;
- tests;
- validation;
- associated commits;
- future considerations.

Change documentation is part of the development process, not an optional release note. Before modifying an established area of the system, developers should consult relevant historical change documents so that previous architectural decisions and constraints are preserved.

A bug fix that exposes an architectural issue should also be documented when it changes or clarifies system behavior or architectural invariants.

## Compliance Gate

Before a release is frozen, the implementation must pass the architecture-principle regression tests in `tests/test_architecture_principles.py` together with the complete existing test suite and the epistemic-state tests.

A passing feature test alone is insufficient when a change can violate an architectural invariant.
