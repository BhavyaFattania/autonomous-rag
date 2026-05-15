# RAG Optimizer Overnight Run Report
**Run ID:** 204f390f-9d92-4527-aa1f-4c450b591483
**Total Cost:** $0.0028
**Experiments Completed:** 3
**Experiments Accepted:** 0

## Best Configuration
```json
{'chunk_size': 1024, 'chunk_overlap': 200, 'top_k': 5, 'hybrid_alpha': 0.5, 'embedding_model': 'openai/text-embedding-small', 'reranker': None, 'reranker_top_n': None, 'generator_model': 'deepseek/deepseek-v4-flash'}
```
**Best Score:** 0.0000

## Successful Patterns

## Failed Patterns
- FAILED_SMOKE: Increasing top_k to 7 and lowering hybrid_alpha to 0.4 may improve recall while balancing retrieval precision.
- FAILED_SMOKE: Adding a reranker will refine the top-6 results to boost precision without losing recall.
- FAILED_SMOKE: Increasing top_k to 10 and hybrid_alpha to 0.7 enhances recall by favoring dense semantic matches over sparse BM25.