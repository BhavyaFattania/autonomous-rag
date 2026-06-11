# Scientist Brain: Input and Output

## Input Prompt
```text
System instructions:
You are an expert retrieval-augmented generation systems researcher.
Your job is to propose the next retrieval architecture configuration to test.

Respond with ONLY a valid JSON object. No preamble. No markdown fences.

The JSON must have exactly these fields:
{
  "hypothesis": "<one sentence, max 120 characters>",
  "node_parser": "<sentence|token|semantic|semantic_double|sentence_window|hierarchical>",
  "retriever": "<dense|bm25|weighted_hybrid_rrf|query_fusion_simple|query_fusion_rrf|auto_merging|sentence_window_dense|recursive>",
  "chunk_size": <integer, one of: 256, 512, 768, 1024, 1536, 2048>,
  "chunk_overlap": <integer, one of: 64, 128, 200, 256, 384>,
  "window_size": <null or integer 1-8>,
  "semantic_threshold": <null or integer 80-99>,
  "semantic_buffer_size": <null or integer 1-3>,
  "top_k": <integer 3-30>,
  "hybrid_alpha": <float 0.0-1.0, step 0.1>,
  "fusion_mode": <null or "simple" or "reciprocal_rerank" or "relative_score">,
  "fusion_num_queries": <null or integer 1-4>,
  "reranker": <null or "CohereRerank">,
  "reranker_top_n": <null or integer 2-10>,
  "embedding_model": "openai/text-embedding-3-small",
  "generator_model": "deepseek/deepseek-v4-flash"
}

Scoring:
- The live loop mostly optimizes fast IR metrics: Recall@K, Precision@K, nDCG@K, and MRR.
- RAGAS context metrics are slow audits, not the main live search signal.
- A high IR score can be misleading if the dataset lacks supporting_titles; prefer configs that also make semantic sense.
- Once recall is saturated, lower top_k can improve Precision@K and sometimes nDCG/MRR.

Parser behavior:
- sentence: stable default chunker. Good baseline, cheap if cached, often lower precision at small top_k.
- token: similar to sentence but token-budgeted. Good for consistent chunk lengths.
- sentence_window: retrieves sentence nodes and returns neighboring window text. Often better context coherence, but creates many nodes.
- hierarchical: creates parent/child nodes. Best for dense, auto_merging, and recursive experiments. Expensive to build but useful when cached.
- semantic and semantic_double: semantically coherent chunks, but very expensive to build. Only use when the exact indexed config is listed as available.

Retriever behavior:
- dense: vector search. Strong for semantic similarity and often best with hierarchical top_k=3-5.
- bm25: sparse lexical search. Good for exact names, entities, and keyword-heavy questions.
- weighted_hybrid_rrf: fuses dense and BM25. Use alpha > 0.5 for dense-heavy, alpha < 0.5 for sparse-heavy.
- query_fusion_simple: combines dense and BM25 scores directly. Use fusion_mode="simple".
- query_fusion_rrf: reciprocal rank fusion over dense and BM25. Use fusion_mode="reciprocal_rerank".
- auto_merging: only with hierarchical. Retrieves child chunks and merges parent context; useful when context coherence matters.
- recursive: only with hierarchical. Follows node references; useful when dense retrieval finds a child but parent context is needed.
- sentence_window_dense: only with sentence_window. Good when exact sentence hit plus nearby context is useful.

Operational rules:
- Do not choose summary_embedding. It is disabled in live search because it builds a large SummaryIndex at retrieval time.
- Do not choose semantic or semantic_double unless that exact parser config appears in Allowed indexed configurations.
- Do not propose a config requiring a new index unless Allowed indexed configurations says new builds are allowed.
- Do not propose an identical config from experiment history.
- Reranking can improve precision but may hurt recall and hit rate limits; use it only around a strong candidate.

Pairing rules:
- auto_merging and recursive require node_parser="hierarchical".
- sentence_window_dense requires node_parser="sentence_window".
- semantic fields are only valid with semantic or semantic_double.
- window_size is only valid with sentence_window.
- fusion fields are only valid with query_fusion_simple or query_fusion_rrf.
- For dense, bm25, weighted_hybrid_rrf, auto_merging, recursive, and sentence_window_dense, set fusion_mode and fusion_num_queries to null.
- If reranker is null, reranker_top_n must be null.
- If reranker is CohereRerank, reranker_top_n must be 2-10 and less than or equal to top_k.

Search guidance:
- If hierarchical top_k=3 has strong precision and recall, explore nearby configs: top_k=4/5, auto_merging, recursive, hybrid alpha=0.7, or reranker_top_n=3.
- If dense configs tie, try BM25 or hybrid only when entity-heavy questions are failing.
- If a family repeatedly scores below best by more than 0.05, move away from it.
- In EXPLORE mode, change parser or retriever family unless the current best is clearly local-search worthy.
- In EXPLOIT mode, modify one or two parameters around the best region.


Current best config:
{
  "chunk_size": 1024,
  "chunk_overlap": 200,
  "top_k": 5,
  "hybrid_alpha": 0.5,
  "embedding_model": "openai/text-embedding-3-small",
  "reranker": null,
  "reranker_top_n": null,
  "generator_model": "deepseek/deepseek-v4-flash"
}

Current best composite retrieval score: 0.0000

Active scoring metric:
Composite retrieval score from Recall@K, Precision@K, nDCG@K, MRR, and periodic
RAGAS context metrics. Prioritize parser, retriever, top_k, hybrid_alpha, and
reranker only when it is likely to improve the retrieval evidence.

Experiment history:
ACCEPTED[1]: High top_k increases recall
ACCEPTED[2]: Hierarchical chunking works better for long docs
REJECTED[1]: BM25 only drops precision
REJECTED[2]: Alpha=0.0 ignores semantics completely

Reflection summary:
We need to try hybrid search with semantic chunking to balance exact match and context.

Allowed indexed configurations:
[
  {
    "embedding_model": "openai/text-embedding-3-small",
    "node_parser": "hierarchical",
    "chunk_size": 512,
    "chunk_overlap": 64
  },
  {
    "embedding_model": "openai/text-embedding-3-small",
    "node_parser": "sentence",
    "chunk_size": 512,
    "chunk_overlap": 128
  },
  {
    "embedding_model": "openai/text-embedding-3-small",
    "node_parser": "sentence",
    "chunk_size": 768,
    "chunk_overlap": 128
  },
  {
    "embedding_model": "openai/text-embedding-3-small",
    "node_parser": "sentence",
    "chunk_size": 1024,
    "chunk_overlap": 200
  },
  {
    "embedding_model": "openai/text-embedding-3-small",
    "node_parser": "sentence_window",
    "chunk_size": 512,
    "chunk_overlap": 64,
    "window_size": 3
  },
  {
    "embedding_model": "openai/text-embedding-3-small",
    "node_parser": "token",
    "chunk_size": 768,
    "chunk_overlap": 128
  }
]

If allowed indexed configurations are listed, choose only one of those
embedding_model/node_parser/chunk_size/chunk_overlap/parser-param combinations.
Other retrieval parameters may vary.

Mode for this experiment: EXPLORE (try something new)

Respond with ONLY the JSON object.
```

## Output Response
```json
{
  "content": "{\n  \"hypothesis\": \"Hierarchical auto_merging can improve context coherence and retrieval for long documents\",\n  \"node_parser\": \"hierarchical\",\n  \"retriever\": \"auto_merging\",\n  \"chunk_size\": 512,\n  \"chunk_overlap\": 64,\n  \"window_size\": null,\n  \"semantic_threshold\": null,\n  \"semantic_buffer_size\": null,\n  \"top_k\": 5,\n  \"hybrid_alpha\": null,\n  \"fusion_mode\": null,\n  \"fusion_num_queries\": null,\n  \"reranker\": null,\n  \"reranker_top_n\": null,\n  \"embedding_model\": \"openai/text-embedding-3-small\",\n  \"generator_model\": \"deepseek/deepseek-v4-flash\"\n}",
  "reasoning": "We need to propose the next retrieval architecture configuration. The JSON must have the required fields, respecting allowed indexed configurations and operational rules. Mode is EXPLORE (try something new). We've had best config from experiment history? The current best composite retrieval score is 0.0000, meaning no positive score yet. The best config given: chunk_size 1024, chunk_overlap 200, top_k 5, hybrid_alpha 0.5, no reranker. But that is an \"initial best\"? It's listed as current best, but score 0.0000 suggests no successful retrieval perhaps. The history includes ACCEPTED[1]: High top_k increases recall; ACCEPTED[2]: Hierarchical chunking works better for long docs; REJECTED[1]: BM25 only drops precision; REJECTED[2]: Alpha=0.0 ignores semantics completely. Reflection summary: We need to try hybrid search with semantic chunking to balance exact match and context. However, we must adhere to allowed indexed configurations. Semantic chunking (parser semantic or semantic_double) is not listed in allowed indexed configurations. So we can't propose semantic. The reflection summary might be a suggestion, but we can't use semantic chunking unless it's in the allowed list. The allowed list has: hierarchical, sentence (two variants), sentence_window with window_size=3, token. No semantic. So we can't propose semantic parser. We need to explore something new. The best config currently (score 0.0) is likely a baseline using sentence 1024/200 with top_k=5, hybrid_alpha=0.5. That's dense? Actually the fields don't include retriever. In the current best config, retriever is missing. It only shows chunk_size, chunk_overlap, top_k, hybrid_alpha, embedding_model, reranker, reranker_top_n, generator_model. So that might be a config with hybrid retriever? Because hybrid_alpha and top_k present. But we need to propose a full config. Since score is 0.0, maybe the retrieval didn't work or we need to explore. ACCEPTED[2] says hierarchical chunking works better for long docs. So we could try hierarchical chunking, which is allowed (one config: hierarchical, chunk_size 512, chunk_overlap 64). But the best config used sentence with chunk_size 1024. We want to explore. So maybe try hierarchical with a retriever like auto_merging or recursive, which requires hierarchical. That would be exploring new retriever families. Auto_merging or recursive are only with hierarchical. That could be an EXPLORE move. The reflection summary wanted hybrid search with semantic chunking, but we can't. So maybe try hybrid search with hierarchical chunking? That could balance exact match and context? But hybrid retriever (weighted_hybrid_rrf) can be used with any index that supports both dense and sparse. For hierarchical index, we can use dense, bm25, or weighted_hybrid_rrf, but NOT auto_merging/recursive if we choose weighted_hybrid_rrf. Because weighted_hybrid_rrf is a separate retriever, not requiring hierarchical specifically. So we could propose a config with hierarchical chunking and weighted_hybrid_rrf, alpha maybe 0.5? But REJECTED[2] says Alpha=0.0 ignores semantics, but we can set alpha something else. The reflection says hybrid search with semantic chunking to balance exact match and context. But we can't use semantic chunking. However, we can use sentence_window or token? Maybe explore sentence_window with sentence_window_dense retriever? That is a retriever that requires sentence_window parser. That's allowed: sentence_window index with chunk_size 512, chunk_overlap 64, window_size 3. We haven't tried sentence_window yet. That could be an explore. Also token index with chunk_size 768, chunk_overlap 128. Could use dense, bm25, or hybrid. So exploring sentence_window with sentence_window_dense might be interesting. That would be a new retriever family (sentence_window_dense) that retrieves sentence nodes and returns window text, potentially improving context coherence. The current best uses sentence parser, so moving to sentence_window is a different parser family. That fits EXPLORE. Also hierarchical could be explored with auto_merging or recursive, but that's also new. Which one? Given that best composite score is 0.0, we need to find something that yields positive scores. Sentence_window_dense might be good for context. But note: window_size is set in index as 3, but we can also specify window_size in config? The parameter window_size is null or integer 1-8. For sentence_window, window_size is the number of sentences on each side to include. The allowed indexed config has window_size: 3 for that index. So we must use that index and set window_size properly? The instruction: \"If allowed indexed configurations are listed, choose only one of those embedding_model/node_parser/chunk_size/chunk_overlap/parser-param combinations.\" So for sentence_window, we must pick chunk_size=512, chunk_overlap=64, and window_size must be 3 (since that's the parser-param specified). Our config must reflect that: node_parser: \"sentence_window\", chunk_size: 512, chunk_overlap: 64, window_size: 3. The semantic_threshold and semantic_buffer_size should be null because not semantic. retriever: sentence_window_dense. top_k: maybe 3-5? Could start with 5 like best earlier. hybrid_alpha etc. null since not hybrid. reranker null. That would be an explore. Also could try hierarchical with auto_merging: node_parser \"hierarchical\", chunk_size 512, chunk_overlap 64, retriever \"auto_merging\", top_k small maybe 5, no hybrid. Could be. ACCEPTED[2] says hierarchical works better for long docs. So hierarchical might be promising. Let's choose hierarchical with auto_merging, as it's a new retriever. But reflection wanted hybrid. Still, we can try auto_merging as explore. Which one is more likely to improve? Score is 0.0, we need a working config. The sentence 1024/200 with hybrid alpha 0.5 likely is the current best but gave 0.0 score? That might mean that config didn't yield any positive retrieval score? That's strange. But maybe the scoring just started and that config got 0.0 composite. So we need to propose a config that could yield a positive score. I'll go with hierarchical auto_merging, because it's a parser we haven't tried, and ACCEPTED[2] suggests it's good for long docs. Also it's an explore move. Set top_k to 5, reranker null. That would be: node_parser \"hierarchical\", chunk_size 512, chunk_overlap 64, retriever \"auto_merging\", top_k 5. Other fields: window_size null, semantic_threshold null, semantic_buffer_size null, hybrid_alpha can be null? For auto_merging, hybrid_alpha is not used, so set null. fusion_mode null, fusion_num_queries null, reranker null, reranker_top_n null. I'll output that. But check requirement: \"If reranker is null, reranker_top_n must be null.\" Yes. So config valid. I'll produce JSON."
}
```
