# Change 0011 — Declarative Reference Resolution Foundation

## Summary

The V1 semantic-context boundary now includes a declarative reference-resolution foundation for lexical references whose referents are supplied by active runtime context.

This change completes the first implementation step for pronoun reference without moving contextual reference logic into the grammar parser.

## Architecture

The pipeline is:

```
Lexicon
  ↓
Reference Anchor
  ↓
Reference Anchor Policy
  ↓
Runtime Context
  ↓
Entity Binding
  ↓
Semantic Representation
```

The grammar remains responsible only for recognizing the pronoun syntactically.

The lexicon declares that a lexical item is a pronoun and names its reference anchor.

The reference-anchor policy declares where that anchor is resolved.

The application injects runtime sources into the resolver.

The semantic parser consumes the resolved entity binding.

## Declarative data

`knowledge/lexicon.json` now declares the user-reference anchor for the existing `i` lexical entry.

`knowledge/reference_anchors.json` declares the anchor policy:

- anchor: `USER`
- runtime source: `USER_PROFILE`
- field: `display_name`

The resolver does not contain knowledge of the spelling or meaning of individual pronouns.

## Runtime identity boundary

Reference resolution does not assert a user statement.

If the active referent does not yet have a named entity handle in user memory, the resolver creates the runtime entity handle needed to bind the reference. This handle is not itself an asserted user fact.

The distinction is:

- runtime identity/reference binding = context infrastructure
- user statement/fact = user memory assertion

## Semantic integration

`SemanticParser` now accepts an optional reference resolver.

When a lexical reference resolves successfully, its existing entity identifier is used directly in the semantic representation rather than generating a new synthetic entity.

This allows:

```
I am tired
```

to become a semantic operation whose subject is the active user's entity.

No pronoun-specific branch was added to the grammar parser.

## Scope

This change intentionally does not implement general anaphora or discourse resolution.

It does not attempt to infer references from:

- previous sentences
- grammatical agreement
- recency
- salience
- world knowledge

Those mechanisms require a separate semantic-context/reference policy and must remain evidence-backed.

## Verification

Dedicated tests cover:

- declarative lexical reference metadata
- anchor-policy resolution
- unknown reference behavior
- semantic binding to the active user entity
- end-to-end storage of a pronoun-subject statement

The complete pytest suite was not executed in this environment, so runtime test success is not claimed.
