# Design Decisions & Tradeoffs

This doc exists to show the reasoning behind the architecture, not just the
architecture itself — and to be explicit about where these choices would
change as the system grows.

## Tenant isolation: RLS vs. schema-per-tenant vs. database-per-tenant

**Chosen: shared schema, `tenant_id` column + Postgres Row-Level Security.**

| Approach | Isolation strength | Ops burden (solo/small team) | Chosen when |
|---|---|---|---|
| Shared schema, app-level filtering only | Weak — one missed `WHERE` clause leaks data | Low | Never for anything handling real customer data |
| Shared schema + RLS (this project) | Strong — enforced by the DB itself | Low-medium | Default choice for most B2B SaaS |
| Schema-per-tenant | Strong | High — migrations must run per-schema, connection pooling gets complicated | Handful of large customers with strict isolation demands |
| Database-per-tenant | Strongest | Very high | Regulatory requirements demanding physical separation |

RLS gets nearly all the isolation guarantee of schema-per-tenant without the
operational multiplication. The honest tradeoff: a single noisy-neighbor
tenant can still affect shared database performance, and a Postgres bug in
RLS itself (rare, but possible) affects everyone. At meaningfully larger
scale, or if a customer's contract specifically requires physical data
separation, database-per-tenant (or at least schema-per-tenant for that one
customer) is the escape hatch — the `tenant_id` design here doesn't block that
migration, it just doesn't require it up front.

## Async processing: Celery vs. Kafka

**Chosen: Celery + Redis.**

Kafka earns its complexity when you have multiple independent consumers of
the same event stream, need replay semantics, or are handling very high
throughput. This system has one producer (the upload endpoint) and one
consumer (the processing worker) — that's a job queue problem, not a
streaming problem. Celery solves it with a small fraction of the operational
surface (no Zookeeper/KRaft, no partition management, one broker that's
already in the stack for caching).

**When this would flip:** if the platform grows additional independent
consumers of "a document was processed" (e.g., a separate analytics
pipeline, a webhook fan-out service, a search-index rebuild service), Kafka's
pub/sub model starts paying for itself. Building on Celery now doesn't
preclude that migration — the task boundary (`process_document_task`) is
already the right seam to introduce an event bus behind, later.

## Embeddings: local model vs. API

**Chosen: local `sentence-transformers` model by default, API model as a
documented alternative — see `docs/EVALS.md` for the actual comparison.**

A local model means zero marginal embedding cost and no tenant document
content leaving the server for embedding — both real arguments in enterprise
sales conversations. The tradeoff is quality: API embedding models
(OpenAI, Voyage) are generally stronger, especially on domain-specific or
non-English text. The eval doc measures this gap directly rather than
asserting it.

## Vector store: pgvector vs. dedicated (Pinecone, Weaviate, Qdrant)

**Chosen: pgvector on the existing Postgres instance.**

One less service to run, back up, and secure — and it inherits RLS-based
tenant isolation for free, since it's just another column on an
already-isolated table. Dedicated vector databases generally offer faster
approximate nearest-neighbor search at very large scale (tens of millions+ of
vectors) and richer filtering/indexing features. pgvector's HNSW index
(introduced in pgvector 0.5+) closes most of that gap for the scale this
project is designed for. Revisit if a single tenant's corpus grows into the
tens of millions of chunks, or if query latency under real load says otherwise
— don't take this doc's word for it, measure it.
