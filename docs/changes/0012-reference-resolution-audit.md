# Change 0012 — Reference Resolution Audit Boundary

## Audit result

The initial reference-resolution foundation is retained as a narrow semantic-context capability.

The audit confirms the intended boundary:

```
Grammar
  → recognizes reference syntax

Lexicon
  → declares lexical reference metadata

Reference Anchor Policy
  → declares runtime source and field

Reference Resolver
  → performs generic binding

Semantic Parser
  → consumes the resulting entity binding

User Memory
  → stores the resulting explicit user statement
```

## No guessing

A lexical reference without:

- a declared anchor,
- an anchor policy,
- an active runtime source, or
- a bound runtime value

remains `UNKNOWN`.

The resolver does not infer an alternative referent.

## No grammar leakage

The grammar remains unchanged by reference resolution.

There is no pronoun-specific grammar branch and no sentence-specific reference rule.

## Current scope

The foundation currently supports the declarative runtime identity reference already represented in the lexicon.

It does not implement general anaphora.

The following remain future semantic-context capabilities:

- discourse antecedent resolution
- recency-based reference
- salience
- grammatical agreement
- cross-sentence pronoun resolution
- ambiguous antecedent handling
- entity reference through descriptive noun phrases

These should only be added after their evidence and policy model is defined.

## Memory boundary

Reference resolution may obtain or create the entity handle required to represent the active runtime referent.

That entity handle is infrastructure for semantic binding; it is not itself an asserted user fact.

The user statement is asserted only through the existing semantic operation and memory execution pipeline.

## Regression contract

The reference audit tests verify:

- lexical anchor declaration
- anchor-policy declaration
- successful runtime binding
- unknown behavior when no anchor exists
- unknown behavior when an anchor is unbound
- semantic binding of `I am tired`
- end-to-end storage of the resulting user statement

The complete pytest suite was not executed in this environment, so runtime test success is not claimed.
