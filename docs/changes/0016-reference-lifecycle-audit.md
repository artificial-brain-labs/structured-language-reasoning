# Change 0016 — Contextual Reference Lifecycle Audit

## Purpose

The contextual reference layer now has an explicit lifecycle contract separating temporary discourse bindings from persistent user knowledge.

## Lifecycle contract

A contextual reference mention may be created only after a successful operation has established an entity mention.

```
Input
  ↓
Parse / Semantic Interpretation
  ↓
Reference Resolution
  ↓
Operation
  ↓
Successful Execution
  ↓
Contextual Reference Mention
```

Failed parsing, unresolved references, ambiguous references, and unsuccessful operations do not create contextual reference mentions.

## Boundaries

### Contextual Reference Memory

Stores temporary structured mention bindings:

- entity identity
- surface form
- grammatical role
- explicit concepts
- evidence trace

It is bounded and disposable.

### User Memory

Stores persistent user knowledge and evidence.

Clearing contextual reference memory must not remove persistent User Memory.

### Transient Communication Memory

Stores raw communication separately from structured reference bindings.

Contextual reference memory is therefore not a replacement for TCM.

## Identity

Contextual mentions store the canonical User Memory entity identity rather than creating independent discourse entities.

This preserves the distinction between:

- surface mention
- canonical entity identity
- persistent knowledge

## Ambiguity

Multiple evidence-supported candidates remain ambiguous.

The lifecycle layer does not introduce recency selection, salience ranking, probability, or heuristic antecedent selection.

Candidate ordering may reflect bounded-memory traversal order for inspection, but ordering is not treated as a resolution score.

## Clarification

When a clarification successfully resumes an original operation, the resulting successful execution participates in contextual reference recording just like any other successful operation.

An unsuccessful clarification or resumed operation does not create contextual reference bindings.

## Capacity

Contextual reference memory is bounded. Eviction affects only temporary discourse context and does not mutate persistent User Memory.

## Verification

Added `tests/test_reference_lifecycle.py` covering:

1. unresolved references do not mutate context
2. ambiguous references preserve context
3. successful statements create mentions
4. capacity eviction
5. context clearing versus persistent User Memory
6. canonical identity
7. failed statements do not create mentions

## Architectural result

The reference subsystem now has three explicit boundaries:

```
TCM
  └── raw communication

Contextual Reference Memory
  └── temporary structured reference evidence

User Memory
  └── persistent asserted / derived knowledge
```

These layers must not be collapsed.
