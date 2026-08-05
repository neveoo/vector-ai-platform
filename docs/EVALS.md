# Retrieval & Classification Evaluation

This is the part most RAG portfolio projects skip entirely — shipping
retrieval without ever measuring whether it's actually good. This doc is the
methodology and results; fill in the results tables as you run the evals.

## Retrieval evaluation

### Method
1. Pick a representative set of ~15-20 real (or realistic synthetic)
   documents across your target document classes (contracts, invoices,
   policies, reports).
2. Hand-write 30-50 questions where you *know* which document(s) and
   ideally which specific chunk should answer each one. This is the
   ground-truth set — `eval/retrieval_test_set.jsonl` (one question,
   expected_document_id, expected_chunk_ids per line).
3. Run `semantic_search()` for each question, check whether the expected
   chunk(s) appear in the top-k results.
4. Report **recall@k** (did the right chunk show up in the top k at all)
   and, if you build reranking, **precision@k** on the reranked order.

### Results — local embedding model (BAAI/bge-small-en-v1.5)

| Metric | Value | Notes |
|---|---|---|
| Recall@5 | _fill in_ | |
| Recall@10 | _fill in_ | |
| Mean query latency | _fill in_ | local model, CPU inference |

### Results — API embedding model (e.g. OpenAI text-embedding-3-small)

| Metric | Value | Notes |
|---|---|---|
| Recall@5 | _fill in_ | |
| Recall@10 | _fill in_ | |
| Mean query latency | _fill in_ | includes network round-trip |
| Cost per 1K documents embedded | _fill in_ | |

### Takeaway
_Write 2-3 sentences once you have real numbers: which model won on quality,
by how much, and whether that gap justifies the cost/privacy tradeoff of
using an API model instead of the local default._

## Chunking strategy comparison (optional, high-signal if you have time)

Re-run the same recall@k eval with:
1. Current: fixed token-window chunking with overlap (`text_extraction.py`)
2. Structure-aware chunking that splits on headings/sections first, then
   token-windows within each section

Even a modest recall improvement here is a good, concrete "here's how I
iterated on RAG quality" story for an interview.

## Classification evaluation

### Method
1. Label ~100-200 example documents with their true class.
2. Split 70/15/15 train/val/test.
3. Compare:
   - **LLM-prompt classification** (`classification.py::_classify_with_llm_prompt`)
   - **Trained classifier**: embeddings + logistic regression (or a small
     fine-tuned transformer) on the same train set
4. Report accuracy, per-class precision/recall, and a confusion matrix for
   both approaches on the same held-out test set.

### Results

| Approach | Accuracy | Latency | Cost per 1K docs |
|---|---|---|---|
| LLM prompt | _fill in_ | _fill in_ | _fill in_ |
| Trained classifier | _fill in_ | _fill in_ | _fill in_ |

### Takeaway
_This comparison — not just "I trained a model" — is the actual signal for
an ML Engineer role: showing you can reason about when a trained model is
worth its added complexity versus when prompting a general model is good
enough._
