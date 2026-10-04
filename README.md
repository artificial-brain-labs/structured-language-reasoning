# Structured Language Reasoning (SLR) V0.3

A transparent, non-LLM language reasoning experiment with ontology, SPO relations, semantic validation, dynamic memory, and a Structured Reasoning State Transition (SRST) foundation.

## Run

```bash
python -m src.main
```

Try:

- The cat eats the mouse.
- What does the cat eat?
- Who eats the mouse?
- The cat does not eat the mouse.

## V0.3 — SRST Foundation

V0.3 adds the foundation for demand-driven structured reasoning without replacing the existing V0.2 language and memory pipeline.

The SRST layer introduces:

- **ReasoningState** — transient working state for goals, claims, evidence, conflicts, assumptions, and validation.
- **Transition** — explicit records of state changes caused by reasoning operators.
- **ProofGraph** — explicit representation of support and derivation.
- **Semantic validation states** — OBSERVED, DERIVED, SUPPORTED, CONTRADICTED, UNKNOWN, and AMBIGUOUS.
- **Termination criteria** — goal satisfaction, sufficient evidence, semantic validity, no unresolved critical conflict, and proof completeness.
- **CognitiveOperator** — an operator contract separating applicability from necessity.
- **OperatorController** — a demand-driven controller that executes an operator only when it is both applicable and necessary.

The SRST implementation lives under `src/reasoning/` and is intentionally separate from `src/reasoner.py`. This preserves the V0.2 behavior while establishing the foundation for incremental integration.

V0.3 does **not** yet implement the six cognitive operators. They will be added after the SRST foundation is validated.
