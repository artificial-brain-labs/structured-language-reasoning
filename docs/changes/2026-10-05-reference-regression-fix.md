# Reference and memory regression fixes

## Changes

- `DynamicMemory.query()` now accepts the semantic `object` keyword as an alias for the internal `object_` parameter, preserving canonical entity filtering.
- Contextual reference candidate selection remains newest-first, while its evidence trace is returned in chronological mention order so resolution priority and auditability are separate concerns.
- Transient contextual mentions are rebound through the persistent identity canonicalizer after successful operations, so explicit identity consolidation updates context without changing the distinction between transient context and persistent user memory.

## Validation intent

These changes address the remaining V1.x regression cases covering object-bound contextual references, mixed agreement evidence, and canonical identity propagation through contextual reference memory.
