# Architecture

Offline-first by design: every stage of the RAG path runs locally and
deterministically, so CI reproduces the exact eval numbers in the README.

## Request path

1. **guardrails (in)** - prompt-injection screen (fail-closed phrase
   match) and PII redaction before anything else touches the input.
2. **hybrid retrieval** - BM25 over chunk text fused with cosine vector
   search via reciprocal rank fusion; deterministic hashing embeddings
   stand in for OCI GenAI embeddings.
3. **generation** - the offline extractive client answers only from
   retrieved chunks and must cite them; `LLMClient` is the seam for a
   real OCI Generative AI endpoint client.
4. **guardrails (out)** - PII redaction on the answer text.
5. **cost track** - token estimate against monthly budget units; the
   guard raises before the budget is exceeded.

Each stage is wrapped in a trace span and metrics timer; a query returns
answer, citations, trace id and a cost receipt.

## OCI footprint (Terraform)

- `modules/genai` - dedicated AI cluster + endpoint with content
  moderation enabled.
- `modules/vector_db` - Autonomous Database 23ai for AI Vector Search;
  mTLS required, 0.0.0.0/0 rejected by variable validation.
- `modules/observability` - notification topic + email subscription,
  GenAI error-count alarm (CRITICAL), log group, monthly budget with an
  80% forecast alert rule.

Mocked-provider `terraform test` asserts the three guardrails that
matter: forecast-based budget alerts, no world-open database, enabled
alarms.

## Quality loop

`fixtures/golden_eval.json` gates every push: recall@k, citation
coverage and token-overlap faithfulness, min pass rate 0.8.
