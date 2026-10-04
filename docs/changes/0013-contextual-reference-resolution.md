# Change 0013 — Contextual Reference Resolution

## Purpose

This change adds a bounded contextual reference layer for references whose antecedent was already established by an earlier structured interaction.

The capability extends the existing declarative runtime reference foundation without moving anaphora rules into the grammar or embedding word-specific logic in Python.

## Architecture

The new boundary is:

```
Grammar
  → recognizes PRONOUN

Lexicon
  → declares reference mode and policy

Contextual Reference Memory
  → retains bounded structured entity mentions

Reference Resolver
  → evaluates evidence-supported candidates

Semantic Parser
  → accepts only a uniquely resolved reference

Semantic Operation
  → executes through the existing memory pipeline
```

The existing Transient Communication Memory remains responsible for raw communication. Contextual Reference Memory is a separate bounded semantic working layer; it does not become persistent knowledge.

## Declarative policy

The lexicon now supports a contextual reference declaration:

- lexical category: `PRONOUN`
- reference mode: `CONTEXTUAL`
- allowed roles: declared by data

The resolver does not contain spellings such as `it`, `he`, or `she`.

## Resolution contract

A contextual reference is:

- `RESOLVED` when exactly one evidence-supported antecedent remains
- `AMBIGUOUS` when multiple candidates remain
- `UNKNOWN` when no candidate exists

The resolver never selects one candidate merely because it is more recent.

No candidate is created as a side effect of unresolved contextual reference resolution.

## Evidence

Candidates come only from structured mentions recorded after successful semantic operations.

Each mention retains:

- entity identity
- surface form
- semantic role
- available concept information

The memory is bounded and temporary.

## Examples

After:

```
cat sleeps
```

the contextual state contains an established `cat` mention. Therefore:

```
dog sees it
```

can resolve `it` to `cat`.

After:

```
cat eats rat
```

both `cat` and `rat` are established candidates. Therefore:

```
it sleeps
```

remains `AMBIGUOUS`.

With no established antecedent:

```
it sleeps
```

remains `UNKNOWN`.

## Memory boundary

Contextual reference memory is not user memory.

It does not:

- assert facts
- create persistent knowledge
- modify ontology
- derive relations
- define identity

It only provides temporary structured evidence for semantic reference binding.

## Semantic safety

An unresolved contextual pronoun is not converted into a newly created entity.

This preserves the invariant:

```
UNKNOWN / AMBIGUOUS ≠ ENTITY
```

Only a resolved reference may enter the semantic operation pipeline.

## Scope

This change does not implement:

- grammatical agreement
- salience scoring
- probabilistic antecedent ranking
- unrestricted recency heuristics
- descriptive noun-phrase reference
- general discourse inference

Those require their own explicit evidence and policy models.

## Regression contract

The contextual reference tests cover:

- unique antecedent resolution
- no antecedent
- multiple antecedents
- no entity creation for unresolved references
- contextual reference used as an object in a later relation

This change preserves the project's no-guessing and data-before-logic principles.
