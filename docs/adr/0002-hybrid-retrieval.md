# ADR 0002: Hybrid retrieval with reciprocal rank fusion

## Status
Accepted

## Context
Pure vector search misses exact-term matches (product names, OCIDs);
pure lexical search misses paraphrases. OCI deployments pair AI Vector
Search with a lexical index for the same reason.

## Decision
Rank chunks with BM25 and cosine vector search independently, then fuse
with RRF (k=60). Weights live in settings so the mix is tunable per
deployment.

## Consequences
- Ranking is deterministic and unit-testable with three-line corpora.
- RRF needs no score normalisation between the two rankers.
- Fusion adds one sort per query; negligible at portfolio scale.
