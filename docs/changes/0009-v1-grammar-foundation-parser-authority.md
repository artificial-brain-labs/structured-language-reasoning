# Change 0009 — V1 Grammar Foundation Becomes the Sole Parser Authority

## Summary

The parser no longer falls back to the superseded `knowledge/grammar.json` rule table.

The authoritative grammar path is now:

`knowledge/grammar_foundation.json`

## Changes

- Changed `Parser` default grammar path from `knowledge/grammar.json` to `knowledge/grammar_foundation.json`.
- Routed the configured grammar path directly into `CompositionalGrammarParser`.
- Removed the legacy procedural rule-table fallback from `Parser`.
- Changed `parse_statement()` to use the compositional parser rather than a second grammar implementation.
- Added a regression test asserting the V1 grammar foundation is the parser authority.
- Removed the superseded `knowledge/grammar.json` file.

## Architectural result

There is now one parser grammar authority:

```
Natural Language
      ↓
Tokenizer
      ↓
grammar_foundation.json
      ↓
CompositionalGrammarParser
      ↓
SemanticComposer
      ↓
Structured Semantic Representation
```

The parser no longer has two competing grammar systems.

This is important for the SLR data-before-logic principle: linguistic structure is declared in the grammar foundation rather than distributed between multiple parser mechanisms.

## Scope

This change does not add new reasoning behavior or expand the declared V1 language subset.

Any construction not represented by the V1 grammar foundation is now explicitly unsupported rather than silently handled by legacy rules.

## Verification

Static consistency was checked while applying the change. The complete pytest suite was not executed in this environment, so runtime test success is not claimed.
