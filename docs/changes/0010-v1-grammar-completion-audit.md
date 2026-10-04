# Change 0010 — SLR V1 Grammar Completion Audit

## Summary

The V1 grammar foundation has been audited against the declared coverage contract.

The audit establishes that the declared V1 grammar subset is syntactically represented by the declarative grammar foundation, including noun phrases, declaratives, negation, interrogatives, and syntactic pronoun subjects.

## Audit decisions

### Pronouns

The pronoun family is now marked `FOUNDATION` for its declared syntactic constructions:

- pronoun subject + transitive verb
- pronoun subject + state

Contextual pronoun reference resolution is explicitly outside the grammar contract. It belongs to the semantic context/reference layer and must not be implemented as sentence-specific grammar logic.

### Legacy metadata

Legacy rule-name metadata was removed from `grammar_foundation.json`. The V1 grammar no longer carries references to the deleted legacy grammar implementation.

### Regression matrix

A V1 grammar matrix was added covering representative instances of:

- bare/entity and determiner noun phrases
- determiner entities
- adjective and multiple-adjective noun phrases
- transitive statements
- state statements
- classification
- identity
- property assignment
- all four declared negation constructions
- all six interrogative constructions
- pronoun subject constructions

Unsupported future families are also checked to remain unparsed rather than guessed:

- coordination
- future tense
- prepositional phrases
- relative/complex clauses

## Architectural conclusion

The current V1 grammar contract is now a syntactic foundation rather than a collection of reactive sentence fixes.

The boundary is:

```
Grammar
  = syntactic structure

Semantic context
  = reference resolution

Ontology
  = domain classification

Reasoning
  = inference from structured knowledge
```

This separation prevents pronoun reference, tense, coordination, or complex-clause semantics from leaking into the grammar parser.

## Verification

The regression matrix and coverage linkage were added to the repository. The complete pytest suite was not executed in this environment, so runtime test success is not claimed.
