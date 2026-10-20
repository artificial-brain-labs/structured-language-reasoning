# SLR V1.x Capability Roadmap

## Purpose

This roadmap defines capability milestones that demonstrate the frozen V1.x architecture without weakening its governing principles. A capability is accepted only when its behavior is specified, evidence and epistemic status remain traceable, and regression tests prove the relevant invariants.

## Baseline

- Architecture baseline: `docs/V1_ARCHITECTURE.md`
- Governing invariants: `docs/ARCHITECTURE_PRINCIPLES.md`
- Baseline recorded in `docs/changes/2026-10-05-v1-architecture-baseline.md`
- Recorded regression result at freeze: **319 passed**
- Implementation remains frozen while the first capability is specified. No implementation behavior is changed by this roadmap.

## Milestone order

1. **Multi-Hop Explainable Reasoning** — produce a proof chain from admissible premises, with explicit support and epistemic status at every step.
2. **Negation and Contradiction Reasoning** — define how explicit negative knowledge, conflicts, and incomplete evidence affect answers.
3. **Complex Reference Resolution** — strengthen multi-turn reference resolution while preserving ambiguity and identity.
4. **Causal Reasoning** — support causal conclusions only when causal relations and inference rules are explicitly represented in data.
5. **Proof-Oriented Responses** — expose concise, machine-checkable or structured evidence-to-answer explanations to callers.

This order is provisional: later milestones must not be implemented until their semantics and acceptance tests are specified. A milestone may be reordered only with a documented rationale.

## Milestone 1: Multi-Hop Explainable Reasoning

### Objective

Demonstrate that SLR can derive a conclusion through more than one admissible reasoning step and show exactly which asserted evidence and declared knowledge support each step.

### Scope for the first increment

The first increment is deliberately bounded to:

- ontology-backed taxonomic inheritance;
- transitive reasoning where transitivity is explicitly declared by relation schema;
- proof chains whose premises are asserted evidence or declared ontology/schema knowledge;
- query-time derivation with provenance preserved;
- explicit separation of asserted, derived, contradicted, ambiguous, and unknown states.

It does **not** authorize arbitrary chaining across different predicates. For example, a chain such as `A IS_A B`, `B NEEDS C` ⇒ `A NEEDS C` is invalid unless a specific, declarative inference rule authorizes that composition. It does not authorize new hard-coded predicate names, word-specific branches, guessed premises, or persistence of derived conclusions as user assertions.

### Reasoning contract

1. **Admissible premises:** asserted user evidence and explicit ontology/relation declarations. Derived edges may be used as intermediate proof steps only when their own support is retained and the underlying inference rule permits it.
2. **No guessing:** missing edges, undeclared rules, or missing ontology links cannot be invented.
3. **Epistemic distinction:** observed/asserted premises remain distinct from derived conclusions. A derivation is never silently promoted to an assertion.
4. **Unknown is not false:** absence of a proof is not proof of negation. If no admissible proof exists, the answer remains unknown or unsupported according to the existing response contract.
5. **Contradiction:** a proof path must not silently erase a relevant contradiction. Contradictory support must be surfaced as conflict, not resolved by arbitrary edge order or confidence alone.
6. **Provenance:** every derived step identifies its immediate premises, inference rule, and transitive support back to source evidence or declared ontology facts.
7. **Determinism:** equivalent graph and rule inputs produce stable proof results and ordering, independent of insertion order where ordering has no semantic meaning.
8. **No graph pollution:** query-time inference does not mutate asserted memory. Derived graph views remain distinguishable from persistent user knowledge.
9. **Bounded execution:** reasoning must terminate on cyclic graphs and must avoid duplicate equivalent conclusions/proofs unless multiple distinct proofs are intentionally exposed.
10. **Explainability:** the answer can be traced through actual graph edges and declared rules; an explanation must not contain a step that the reasoner did not execute.

### Proof representation

The implementation proposal should define a structured proof-step representation with, at minimum:

- conclusion subject, predicate, and object;
- epistemic/status classification;
- rule identifier and rule source;
- immediate premise references;
- source evidence identifiers or ontology/schema provenance;
- ordered proof path or dependency references.

Do not introduce a second canonical graph or independent fact store to hold proofs. The proof representation should refer to the existing canonical `SemanticGraph` and `SemanticGraphReasoner` outputs.

### Required tests

- A conclusion requiring at least two admissible inference steps is derived.
- Every proof step has valid premises and an identified rule.
- The final conclusion traces to original asserted evidence and declared ontology data.
- No derived conclusion is persisted as an asserted user fact.
- Missing intermediate knowledge yields UNKNOWN/unsupported, not a guessed conclusion.
- A negative fact does not arise from mere absence of a positive fact.
- Relevant contradictory evidence is preserved and surfaced.
- Cross-predicate composition is rejected unless a declarative rule explicitly allows it.
- Cycles terminate without unbounded traversal.
- Duplicate routes do not create duplicate equivalent conclusions.
- Results are stable across semantically equivalent insertion orders.
- Existing architecture-principle and full regression suites remain green.

### Acceptance gate

The milestone is accepted only when:

- the behavior and proof schema are documented;
- all required tests pass;
- existing architecture principles remain unchanged;
- the full test suite passes;
- no hard-coded linguistic/domain knowledge is added to Python;
- the implementation adds no competing reasoning kernel or independent asserted-fact store;
- the implementation change is recorded in `docs/changes/` with rationale, behavior, tests, and known limitations.

The frozen **319-pass** result is a historical baseline, not a claim about tests after future changes. Record the actual local test result for each implementation milestone.

## Design gate before implementation

Before writing implementation code, review the existing `SemanticGraph`, `SemanticGraphReasoner`, graph builder, query path, relation schema, and ontology representation against this contract. Identify the smallest missing capability, propose the proof data shape, and add tests before changing production behavior. Do not assume the current implementation already supports arbitrary multi-hop composition.

## Completion criteria for the roadmap

Each milestone must have a written scope, prohibited inferences, proof/evidence requirements, tests, and explicit acceptance criteria. Keep the V1.x architecture frozen except for narrowly scoped, tested capability increments that preserve its invariants.
