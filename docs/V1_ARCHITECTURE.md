# SLR V1.x Architecture

## Status

This document describes the architecture represented by the current V1.x implementation. It complements the governing invariants in `docs/ARCHITECTURE_PRINCIPLES.md`.

## 1. System boundary

SLR is a transparent, data-driven language reasoning system. It does not treat the language model itself as the source of knowledge. Language is transformed into structured representations using declarative grammar and lexical knowledge; user knowledge is then stored, evidenced, projected, and reasoned over.

The architecture is:

```
Natural Language
    ↓
Lexical Structure
    ↓
Declarative Grammar
    ↓
Semantic Representation
    ↓
Epistemic Interpretation
    ↓
User Memory + Evidence
    ↓
Semantic Graph Projection
    ↓
Canonical Graph Reasoning
    ↓
Query / Proof / Response
```

## 2. Declarative knowledge layer

The system keeps domain and linguistic knowledge outside procedural mechanisms wherever practical.

Primary declarations include:

- `knowledge/lexicon.json` — lexical concepts and features;
- `knowledge/grammar_foundation.json` — compositional grammar;
- ontology data — taxonomic knowledge and inherited properties;
- `knowledge/relations.json` — relation roles and semantic constraints;
- `knowledge/execution_policies.json` — execution and memory-boundary policy;
- operation definitions, response policies, clarification policies, and reference policies.

Python components provide generic mechanisms for interpreting these declarations. New normal linguistic or domain concepts should not require word-specific procedural branches.

## 3. Language-to-semantics pipeline

```
Input
  ↓
Tokenizer
  ↓
CompositionalGrammarParser
  ↓
SemanticComposer
  ↓
SemanticParser
  ↓
SemanticOperation(s)
```

The parser derives structure from the declarative grammar. Unsupported constructions remain unparsed rather than being guessed.

Ambiguous constructions remain ambiguous until sufficient evidence exists to resolve them.

## 4. Epistemic pipeline

User communication is tracked through explicit epistemic states:

```
OBSERVATION
     ↓
INTERPRETATION
     ↓
ASSERTION
     ↓
DERIVATION / HYPOTHESIS
```

These states have different meanings and are not interchangeable.

An assertion requires explicit confirmation. A derivation may explain an answer but does not become an asserted user fact automatically.

## 5. Memory boundary

### User Memory

User memory is the durable store for explicit user-specific knowledge, including:

- facts;
- classifications;
- relationships;
- identity statements;
- evidence and provenance.

### Transient Communication Memory

TCM is bounded temporary communication state. It stores raw interaction material for the active context and may decay or be cleared independently.

### Contextual Reference Memory

Contextual reference memory stores temporary entity mentions used for reference resolution. It follows canonical identity when explicit identity consolidation occurs, but it does not replace persistent user memory.

## 6. Semantic graph

The semantic graph is a projection of user memory and derived reasoning results.

```
User Memory
    ↓
Asserted Graph
    ↓
Graph Reasoner
    ↓
Derived Graph
```

The graph is not an independent knowledge source.

Asserted edges retain evidence provenance. Derived edges retain support and the mechanism/rule responsible for their derivation.

## 7. Canonical reasoning

`SemanticGraphReasoner` is the canonical V1.x graph reasoning mechanism.

Reasoning starts from asserted graph edges. Ontology inheritance and declarative relation semantics produce derived edges without mutating asserted user memory.

For example:

```
Tom IS_A CAT          ASSERTED
       ↓
CAT IS_A FELINE       DERIVED
       ↓
FELINE IS_A MAMMAL    DERIVED
       ↓
MAMMAL IS_A ANIMAL    DERIVED
```

The resulting proof remains traceable to the original assertion.

Legacy reasoning or graph interfaces retained for compatibility must delegate to the canonical implementation rather than maintain competing reasoning state.

## 8. Execution boundary

Semantic operations are routed through generic execution mechanisms.

```
Semantic Operation
       ↓
Statement Router
       ↓
Operation Engine
       ↓
Execution Policy
       ↓
User Memory / Relationship Memory
```

The execution policy determines how subjects and objects are resolved, whether relation validation applies, and whether clarification is required.

## 9. Reference resolution

Reference resolution is evidence-driven.

Candidate selection may prioritize recent contextual mentions, while the evidence trace remains auditable. Agreement compatibility, role, prior mention, and declared reference policy constrain resolution.

The system does not select a candidate merely because it is plausible.

When exactly one candidate satisfies the declared constraints, the reference may resolve. Multiple compatible candidates remain ambiguous; no compatible candidate remains unresolved.

## 10. Identity

Identity is represented explicitly through the declarative `SAME_AS` relation.

Canonicalization provides stable identity for memory queries, graph projection, and transient contextual references.

Identity consolidation does not require duplicating or rewriting every historical observation.

## 11. Query and proof

Queries operate against the canonical graph representation and may trigger derivation at query time.

A successful derived answer should expose:

- the asserted starting evidence;
- derived intermediate steps;
- the applicable derivation rule;
- support linking derived steps back to the asserted evidence.

This makes the answer inspectable rather than opaque.

## 12. Architectural invariants

The architecture must preserve:

1. No guessing.
2. Unknown is not false.
3. Data before logic.
4. User knowledge is isolated.
5. Derived knowledge is not asserted knowledge.
6. Explicit classification remains explicit evidence.
7. Ontology supplies inheritance.
8. The semantic graph remains a projection.
9. Reasoning remains explainable.
10. Clarification preserves identity and context.
11. Epistemic state remains explicit.
12. Assertions require explicit confirmation.
13. TCM remains transient.
14. There is one canonical graph and reasoning kernel.
15. Evidence remains traceable.
16. Meaningful architectural changes are documented.

## 13. V1.x validation baseline

The architecture is currently backed by the complete regression suite:

```
319 passed in 1.63s
```

This result is the V1.x regression baseline at the time this architecture document was established.

Future changes to established architectural areas should first preserve this baseline, then add or revise tests deliberately when behavior is intentionally changed.
