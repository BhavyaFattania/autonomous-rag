# Autonomous RAG Optimizer

An intelligent, autonomous system designed to iteratively hyper-optimize Retrieval-Augmented Generation (RAG) pipelines over an extended period (such as overnight). Powered by LangGraph, LlamaIndex, ChromaDB, and evaluated with Ragas.

## 🚀 Features

- **Autonomous Experimentation Loop:** Proposes, tests, and evaluates different RAG configurations (chunk size, overlap, retrieval strategies) entirely unattended.
- **LangGraph Orchestration:** Utilizes a highly robust state machine to handle validation, deduplication, budget guarding, smoke testing, and deep evaluations.
- **Strict Budget Guarding:** Intercepts and monitors LLM (OpenRouter) API costs to prevent runaway billing during long-running optimization sessions.
- **Resilient Evaluation Threading:** Offloads blocking, synchronous evaluation frameworks (like RAGAS) to background threads using `nest_asyncio` and `ThreadPoolExecutors` for non-blocking I/O operations.
- **Comprehensive SQLite Storage:** Retains every experiment, caching failures and baseline scores to continuously track progress and avoid redundant executions.

## 🛠️ Tech Stack

- **Python:** `^3.11`
- **Orchestration:** `langgraph`, `langchain-core`
- **RAG & Vector Stores:** `llama-index` (modular), `chromadb`
- **Evaluation:** `ragas`, `datasets`
- **Database:** SQLite (`aiosqlite`)
- **Dependency Management:** Poetry

## 📦 Getting Started

### Prerequisites
- Python 3.11+
- Poetry installed (`pip install poetry`)
- OpenRouter/OpenAI API Keys

### Installation

1. Clone the repository and install dependencies using Poetry:
   ```bash
   poetry install
   ```

2. Set up your environment variables by creating a `.env` file in the root directory:
   ```env
   OPENAI_API_KEY=your_openai_key
   OPENROUTER_API_KEY=your_openrouter_key
   # Add any other required environment variables based on pydantic settings
   ```

3. Run the overnight optimization script:
   ```bash
   poetry run python run_overnight.py
   ```

## 📖 Documentation

For detailed insights into the system, please refer to the following documentation:
- [System Architecture](docs/architecture.md): Deep dive into the LangGraph loop, nodes, and the internal operations of the Evaluator.
- [Developer Guide](docs/developer_guide.md): Information on setting up the dev environment, testing, and extending the orchestration graph.
