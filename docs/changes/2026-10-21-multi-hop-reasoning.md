# Change Record: Multi-Hop Explainable Reasoning Specification

- **Date:** 2026-10-21
- **Branch:** `v1.0-development`
- **Type:** Capability specification and planning
- **Implementation status:** Not started
- **Architecture status:** V1.x foundation remains frozen

## Decision

Define Multi-Hop Explainable Reasoning as the first V1.x capability milestone. The objective is to demonstrate inference across multiple admissible steps while preserving proof provenance and epistemic status throughout the chain.

The specification is maintained in `docs/V1_CAPABILITY_ROADMAP.md`.

## Scope established

The first increment is limited to:

- ontology-backed taxonomic inheritance;
- explicitly declared transitive relations;
- proof steps tied to actual graph premises and declared rules;
- traceability to asserted evidence and ontology/schema declarations;
- explicit handling of UNKNOWN and contradictory support;
- query-time derivation that does not promote derived conclusions into asserted user memory.

Arbitrary cross-predicate composition is out of scope unless a declarative inference rule explicitly authorizes it.

## Constraints

This decision does not authorize:

- sentence- or word-specific Python branches;
- hard-coded domain or linguistic facts;
- inference from missing information;
- treating UNKNOWN as FALSE;
- silently resolving contradictions;
- persisting derived conclusions as user assertions;
- introducing a second canonical graph, independent fact store, or competing reasoning kernel.

## Required verification

Before implementation is accepted, tests must cover multi-step proof construction, provenance, unknowns, negation/absence distinction, contradictions, unauthorized cross-predicate composition, cycles, duplicate conclusions, deterministic results, and compatibility with the existing architecture-principle and full regression suites.

The recorded architecture freeze result is **319 passed**. This is a historical baseline only; it is not a test result for any implementation of this milestone.

## Files changed

- Added `docs/V1_CAPABILITY_ROADMAP.md`.
- Added this change record.

No production code, runtime behavior, or existing tests were changed in this documentation-only step.
