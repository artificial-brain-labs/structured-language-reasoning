# State Statement and Context Recency Fix

## Date
2026-10-05

## Changes

- Added a declarative `NP + STATE -> STATEMENT` grammar production so simple state statements such as `cat sleeps` can enter the normal semantic and memory pipeline.
- Restored newest-first ordering for bounded contextual-reference candidates. Recent mentions are considered before older mentions.
- Updated the V1 grammar-foundation unsupported-construction test to reflect that noun-phrase coordination is now supported.

## Architectural intent

These changes preserve the SLR data-driven architecture:

- grammar capability remains declared in `knowledge/grammar_foundation.json`;
- contextual recency remains a property of transient communication memory;
- no sentence-specific parsing or reference-resolution logic was added to Python;
- unsupported constructions remain unparsed rather than guessed.
