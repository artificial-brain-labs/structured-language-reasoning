# Change 0022 — Declarative Coordination Foundation

## Purpose

SLR now supports noun-phrase coordination as a declarative grammar construction.

The foundation construction is `NP → NP CONJUNCTION NP`, with lexical conjunction `and`.

Coordination is represented structurally before semantic execution.

## Semantic execution

A coordinated subject or object expands into independent semantic operations.

Examples:
- `cat eats rat and mouse` → `cat EATS rat` and `cat EATS mouse`.
- `cat and dog eat rat` → `cat EATS rat` and `dog EATS rat`.

When both subject and object are coordinated, the semantic representation is the declarative Cartesian expansion of the coordinated members.

## Architectural boundaries

Coordination is not implemented with sentence-specific parsing logic. The grammar declares the coordination production and its member positions. The parser exposes those members generically. Semantic composition expands them into operations. Execution remains unchanged at the domain-operation layer.

No inference is performed by coordination.

## Coverage

`coordinated_noun_phrase` is now FOUNDATION. `coordinated_statement` and `coordinated_adjective` remain PLANNED.

## Verification

Regression tests cover coordinated subject and object execution.

No complete test-suite result is claimed in this change record.
