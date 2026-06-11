# 🤖 The Autonomous RAG Optimizer: A Complete Walkthrough

Welcome to your Autonomous RAG Optimizer! You have just built a state-of-the-art AI system capable of "self-improving" its own architecture without human intervention. 

Here is exactly what this project is, how it works, and what happens when you press "Run".

---

## 🎯 The Core Problem
When engineers build a **RAG (Retrieval-Augmented Generation)** application, they have to manually guess the best settings (hyperparameters). Should the document `chunk_size` be 512 or 1024? Should we use `text-embedding-3-small` or `cohere-v3`? Should we fetch the top 3 or top 10 documents? 

Finding the best combination manually is tedious, slow, and mathematically exhausting. 

**This project automates that entire job.** You turn it on when you go to sleep, and by the time you wake up, an AI has tested dozens of combinations and found the mathematically optimal configuration for your dataset.

---

## 🧠 The AI "Scientist"
At the heart of your project is an AI Scientist powered by the **DeepSeek V4 Pro** model (acting with high reasoning effort). 

The Scientist is given a prompt that says: *"Here is our current best RAG configuration and its score. Propose a new configuration that you think will score higher, and explain your hypothesis."*

The Scientist then spits out a JSON config to test, for example:
> **Hypothesis:** *"Increasing chunk_size to 1024 while maintaining a high overlap of 256 will capture more context for complex comparison questions."*

---

## 🔄 The Execution Loop (LangGraph)
Once the Scientist proposes a new config, the **LangGraph Orchestrator** takes over. It acts as a massive state-machine pipeline. Here is the step-by-step lifecycle of a single experiment:

1. **Validation & Deduplication:** The orchestrator checks if the config is valid and makes sure we haven't already tested it (to save money).
2. **Indexing (`src/indexer`):** If the Scientist proposed a new chunk size, the system actually chunks the raw Wikipedia dataset (`data/corpus/hotpotqa_paragraphs.jsonl`) and creates a brand new Vector Database collection in your Qdrant cluster on the fly.
3. **Smoke Test (`src/rag_pipeline`):** It runs 5 quick questions through the pipeline to make sure the AI doesn't crash or hallucinate gibberish.
4. **Full Evaluation (`src/evaluator`):** It runs 50 benchmark questions against the vector database. It then uses a framework called **RAGAS** (with an AI Judge model) to grade the pipeline on 4 metrics:
   - *Faithfulness* (Did it hallucinate?)
   - *Answer Relevancy* (Did it actually answer the question?)
   - *Context Recall* (Did the vector database fetch the right documents?)
   - *Context Precision* (Were the right documents ranked at the top?)
5. **Acceptance:** If the new config gets a higher weighted score than the baseline, it becomes the new "Best Config".
6. **Logging:** Everything is saved to a local SQLite database (`experiments.sqlite`), and the Scientist is given the results to learn from for its next hypothesis!

---

## 💰 The Budget Guard
Because AI API calls cost money, the system has a strict `cost_tracker.py`. It calculates the exact fraction-of-a-penny cost of every single prompt sent to OpenRouter. 

If the total cost of your overnight run hits **$10.00**, the LangGraph orchestrator immediately triggers a kill-switch, safely aborting the run and generating a final report so you never wake up to an unexpected bill.

---

## 🕹️ What It Feels Like to Run
When you start the system (`python -m scripts.run_overnight`), your terminal becomes a command center. You will see logs streaming in as the Scientist thinks, the vector database builds indices, and the evaluator grades the answers. 

It feels like you are watching a team of engineers work at 100x speed. At the end of the run, you will find an `overnight_run_report.md` file detailing exactly what the AI learned, what failed, and what your final, optimized RAG architecture should be!
