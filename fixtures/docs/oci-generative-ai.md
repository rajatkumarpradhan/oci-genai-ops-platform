# OCI Generative AI

OCI Generative AI is a fully managed service that provides access to
large language models from Cohere and Meta Llama families. Models run
on dedicated AI clusters backed by GPU infrastructure in an OCI region.

Dedicated AI clusters isolate customer workloads and give predictable
throughput for inference and fine-tuning. Fine-tuning uses the T-Few
technique to update a small set of parameters efficiently.

The service exposes chat, text generation, summarization and embedding
endpoints. Embeddings power retrieval augmented generation when paired
with a vector store such as Oracle Database 23ai AI Vector Search.
