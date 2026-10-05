# Structured Language Reasoning (SLR) V1.x

A transparent, data-driven language reasoning system that converts natural language into structured semantic representations, maintains explicit user knowledge with evidence provenance, projects that knowledge into a canonical semantic graph, and performs explainable reasoning without guessing.

## V1.x Architecture

```
Natural Language
      ↓
Declarative Grammar + Lexicon
      ↓
Semantic Composition
      ↓
Epistemic Interpretation
      ↓
User Memory + Evidence Ledger
      ↓
Semantic Graph Projection
      ↓
Canonical Graph Reasoning
      ↓
Validated Query / Explanation
```

### Architectural boundary

```
Grammar / Lexicon / Ontology / Relations / Policies
                         │
                         ▼
                  SLR Interpretation
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
         User Memory              TCM
              │                     │
              └──────────┬──────────┘
                         ▼
                  Semantic Graph
                         │
                         ▼
              Canonical Graph Reasoner
                         │
                         ▼
                   Query / Proof
```

### Core principles

- **No Guessing** — missing information remains unknown.
- **Unknown Is Not False** — absence of knowledge is not negation.
- **Data Before Logic** — grammar, lexicon, ontology, relations, policies, and operations are declarative.
- **User Knowledge Belongs to User Memory** — system knowledge is not mutated by user assertions.
- **Derived Knowledge Is Not Asserted Knowledge** — inference does not silently become fact.
- **Explicit Classification Is Evidence** — classification is represented as explicit knowledge rather than silently changing identity.
- **Semantic Graph Is a Projection** — the graph is not a second source of truth.
- **Reasoning Is Explainable** — derived conclusions retain supporting evidence and rules.
- **Epistemic State Is Explicit** — observation, interpretation, assertion, derivation, and hypothesis remain distinct.
- **Transient Communication Memory** — temporary communication context is separated from enduring user knowledge.

See [docs/ARCHITECTURE_PRINCIPLES.md](docs/ARCHITECTURE_PRINCIPLES.md) for the governing invariants and [docs/V1_ARCHITECTURE.md](docs/V1_ARCHITECTURE.md) for the current architecture.

## Run

```bash
python -m src.main
```

## Validation

The V1.x regression baseline is:

```text
319 passed
```

The full suite must remain green before an established architectural area is considered stable.

## Project status

The `v1.0-development` branch is the active V1.x development line. Changes to established architecture should preserve the principles documented in `docs/ARCHITECTURE_PRINCIPLES.md` and be recorded under `docs/changes/`.
