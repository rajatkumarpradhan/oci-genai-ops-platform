# ADR 0001: Offline-first platform design

## Status
Accepted

## Context
The platform demonstrates OCI GenAI operations without a live tenancy,
credentials or spend. Production-fidelity demos usually fake screenshots;
that is dishonest and untestable.

## Decision
Every stage runs offline behind a seam that mirrors the OCI shape:
hashing embeddings behind the embedder interface, in-memory vector store
behind upsert/search/persist, extractive generator behind `LLMClient`,
mocked OCI provider for Terraform.

## Consequences
- CI reproduces exact eval numbers on every push.
- Swapping in real OCI services is an interface-local change per seam.
- The embedder is lexical, so retrieval quality on real corpora will be
  lower than with OCI GenAI embeddings; this is documented, not hidden.
