# Change 0019 — Explicit Agreement Attributes

## Purpose

SLR now has a data representation for explicit grammatical agreement attributes without activating agreement-based reference resolution.

The change separates:

1. **Lexical agreement** — attributes explicitly declared by a lexical entry.
2. **Entity agreement** — attributes carried by a semantic entity.
3. **Contextual mention agreement** — attributes explicitly attached to a temporary discourse mention.

## Declarative data

The lexicon now declares agreement only where it is explicit:

- `i`: `number=SINGULAR`, `person=FIRST`
- `it`: `number=SINGULAR`, `person=THIRD`

Other lexical entries do not receive inferred agreement.

The absence of an attribute means **unknown**, not a guessed value.

## Entity model

Semantic `Entity` now carries an optional `agreement` mapping.

The semantic parser copies only explicitly declared lexical agreement into newly created entities.

A resolved contextual reference does not invent agreement for its antecedent.

## Contextual reference model

`ReferenceMention` can carry explicit agreement attributes as structured data.

The values are stored canonically as a tuple of key/value pairs so the bounded contextual memory remains immutable per mention.

## Enforcement boundary

This change does **not**:

- rank antecedents by agreement
- reject antecedents by agreement
- infer agreement from noun morphology
- infer gender
- infer agreement from ontology classes
- resolve ambiguity using agreement

Agreement remains data, not reasoning.

## Architectural rule

Unknown agreement must remain unknown until an explicit source establishes it.

The intended future boundary remains:

```
Explicit Agreement Data
        +
Reference Evidence
        +
Reference Policy
        ↓
Reference Compatibility
```

Any compatibility enforcement must be introduced as a separate documented change.

## Verification

Added regression coverage for:

- lexical agreement retrieval
- explicit entity agreement preservation
- contextual mention agreement
- preservation of unknown agreement
