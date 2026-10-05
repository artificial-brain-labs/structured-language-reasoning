# V1.x Architecture Baseline — 2026-10-05

## Decision

Freeze the current SLR V1.x implementation as an architectural regression baseline before adding new capabilities.

## Baseline

The complete test suite passes:

```
319 passed in 1.63s
```

## Verified areas

The baseline covers the current architecture including:

- declarative grammar and compositional parsing;
- ambiguity and no-guessing behavior;
- semantic composition and structured operations;
- explicit epistemic evidence;
- user-memory isolation;
- transient communication memory;
- contextual reference resolution and evidence traces;
- canonical identity handling;
- declarative relation and execution policies;
- semantic graph projection;
- canonical graph reasoning;
- ontology inheritance;
- derived-query behavior;
- proof and evidence traceability;
- clarification lifecycle;
- data-only domain extension;
- compatibility facades without competing reasoning state.

## Architectural decision

No implementation refactor is required as part of this baseline.

Future work should:

1. preserve the documented architectural invariants;
2. keep the complete regression suite green;
3. add tests for intentional new behavior;
4. document meaningful architectural or externally observable changes under `docs/changes/`.

## Documentation alignment

The README and `docs/V1_ARCHITECTURE.md` now describe the V1.x architecture represented by the implementation. Historical V0.x documents remain as historical architecture records and are not treated as the current V1.x specification.

## Future consideration

New capabilities should be evaluated against the V1.x boundary before implementation, especially if they affect language interpretation, memory, identity, graph semantics, reasoning, epistemic state, or governance.
