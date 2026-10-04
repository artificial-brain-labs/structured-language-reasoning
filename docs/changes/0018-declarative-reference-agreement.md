# Change 0018 — Declarative Reference Agreement Model

## Purpose

SLR now has a formal data model for future grammatical agreement constraints in reference resolution.

This change deliberately defines the contract without activating heuristic agreement resolution.

## Agreement dimensions

The reference policy contract currently recognizes:

- `number`
- `person`
- `gender`

These are declarative dimensions only.

No lexical entry currently supplies agreement values, and no resolver currently ranks or rejects antecedents based on these dimensions.

## Enforcement boundary

Every reference mode declares:

```json
"agreement": {
  "dimensions": ["number", "person", "gender"],
  "enforcement": "DECLARATIVE_ONLY"
}
```

The only supported enforcement mode is `DECLARATIVE_ONLY`.

Any future enforcement mechanism must be explicitly introduced as a separate architectural change.

## Why this matters

The system now distinguishes:

1. **Agreement model** — what dimensions may exist.
2. **Agreement data** — what a lexical/entity/reference expression explicitly declares.
3. **Agreement enforcement** — whether and how compatibility is evaluated.

These must not be collapsed.

## Current behavior

Reference resolution remains evidence-based.

Therefore:

- agreement is not inferred
- gender is not guessed
- number is not guessed
- person is not guessed
- agreement does not break ambiguity
- agreement does not create an antecedent

The current contextual reference resolver continues to rely only on its declared evidence contract.

## Architectural direction

Future reference compatibility can eventually become:

```
Grammar Structure
      +
Reference Policy
      +
Explicit Agreement Data
      +
Reference Evidence
      ↓
Reference Compatibility
```

But compatibility must remain declarative and explainable.

## Verification

Added policy tests covering:

- declared agreement dimensions
- unsupported agreement dimensions
- rejection of heuristic agreement enforcement

No runtime reference-resolution behavior was changed by this contract.
