# Change 0017 — Grammatical Reference Contract

## Purpose

Reference resolution now has an explicit grammatical contract connecting lexical reference modes with grammatical roles.

## Declarative layers

The contract is represented across:

```
Lexicon
  ↓
Reference Policy
  ↓
Grammar Reference Roles
  ↓
Reference Resolver
```

Lexical metadata declares what kind of reference an expression represents.

Reference policy declares which grammatical roles that reference mode may occupy.

Grammar productions declare which semantic roles are reference-compatible.

## Grammar metadata

Grammar productions containing semantic roles may declare:

```json
"reference_roles": {
  "subject": ["CONTEXTUAL", "ANCHOR"],
  "object": ["CONTEXTUAL", "ANCHOR"]
}
```

The declaration is attached to the production rather than implemented as sentence-specific Python logic.

## Validation

The reference policy validator now checks:

- every declared reference role is an actual grammatical role
- every declared reference mode exists in the reference policy
- reference-mode declarations are non-empty
- lexical reference metadata remains valid

The lexicon load path performs the complete validation.

## Architectural significance

This creates a formal contract between language structure and reference semantics without introducing:

- recency heuristics
- salience scoring
- probabilistic antecedent selection
- gender/number guessing
- sentence-specific exceptions

The grammar says **where a reference may structurally occur**.

The reference policy says **what reference modes are permitted there**.

The contextual reference memory supplies **evidence for which entity may satisfy the reference**.

The resolver returns UNKNOWN or AMBIGUOUS when the evidence is insufficient.

## Scope

This is a compatibility contract and validation layer. It does not yet add finer-grained grammatical agreement or semantic role restrictions.

Those should be introduced only as declarative extensions when their linguistic contract is explicitly defined.
