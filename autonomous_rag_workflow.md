# Autonomous RAG Optimizer Workflow

The following flowchart illustrates the entire lifecycle of the autonomous optimization process as executed by `run_overnight.py` and orchestrated by LangGraph. It maps out the three primary phases: System Initialization, the iterative Graph execution loop, and the internal operations of the Evaluator node.

```mermaid
flowchart TD
    %% Styling
    classDef init fill:#f9f2ec,stroke:#b08d6a,stroke-width:2px,color:#333
    classDef graphLoop fill:#e6f3ff,stroke:#4a90e2,stroke-width:2px,color:#333
    classDef evalDeep fill:#e8fae6,stroke:#5cb85c,stroke-width:2px,color:#333
    classDef failState fill:#ffe6e6,stroke:#d9534f,stroke-width:2px,color:#333
    classDef terminal fill:#333,stroke:#fff,stroke-width:2px,color:#fff

    %% 1. Initialization
    subgraph Initialization [1. System Initialization & Baseline]
        direction TB
        Start([Start run_overnight.py]) ::: terminal --> InitDB(Init SQLite DB & WAL Mode) ::: init
        InitDB --> InitCost(Init Cost Tracker) ::: init
        InitCost --> LoadConfig(Load Settings & Baseline) ::: init
        LoadConfig --> CheckCache{Baseline Cached?} ::: init
        
        CheckCache -- "Cache Miss" --> EvalBase[Phase 0: Evaluate Baseline Config] ::: init
        EvalBase --> SaveCache[Save Baseline Score] ::: init
        CheckCache -- "Cache Hit" --> SetState[Initialize LangGraph State<br/>run_id, baseline_score, etc.] ::: init
        SaveCache --> SetState
    end

    %% 2. LangGraph Loop
    subgraph Graph [2. Autonomous LangGraph Execution Loop]
        direction TB
        StateInit((Graph Start)) ::: graphLoop --> Scientist
        
        Scientist[Scientist Node<br/>Propose new RAG Config & Hypothesis] ::: graphLoop
        Scientist --> Validator[Validator Node<br/>Check config bounds & types] ::: graphLoop
        
        Validator -- "Valid" --> Deduplicator[Deduplicator Node<br/>Check config hash in DB] ::: graphLoop
        Validator -- "Invalid" --> HandleFail[Failure Handler<br/>Record FAILED_VALIDATION] ::: failState
        
        Deduplicator -- "Unique" --> BudgetGuard[Budget Guard Node<br/>Check OpenRouter API Cost] ::: graphLoop
        Deduplicator -- "Duplicate" --> HandleFail
        
        BudgetGuard -- "Within Budget" --> Indexer[Indexer Node<br/>Build ChromaDB Index] ::: graphLoop
        BudgetGuard -- "Budget Exceeded" --> ReportWriter
        
        Indexer --> SmokeTest[Smoke Test Node<br/>Run 2 Basic Queries] ::: graphLoop
        SmokeTest -- "Pass" --> Evaluator[Evaluator Node<br/>Full Context Retrieval & Evaluation] ::: graphLoop
        SmokeTest -- "Fail" --> HandleFail
        
        Evaluator -- "Success" --> Acceptance[Acceptance Node<br/>Compare vs Best Score] ::: graphLoop
        Evaluator -- "Timeout/Error" --> HandleFail
        
        Acceptance --> Recorder[Recorder Node<br/>Commit results to SQLite] ::: graphLoop
        HandleFail --> Recorder
        
        Recorder --> Reflection[Reflection Node<br/>Analyze Success/Fail Patterns] ::: graphLoop
        
        Reflection --> Condition{Max Exp Reached?} ::: graphLoop
        Condition -- "No" --> Scientist
        Condition -- "Yes" --> ReportWriter[Report Writer Node<br/>Generate Markdown Report] ::: graphLoop
    end

    %% 3. Evaluator Deep Dive
    subgraph EvalInternals [3. Evaluator Node Execution Path]
        direction TB
        EvalStart((Eval Node Entry)) ::: evalDeep --> SelectQ[Select 5 Eval Questions] ::: evalDeep
        SelectQ --> LoopRuns{For run in 1..n_runs} ::: evalDeep
        
        LoopRuns --> Retrieve[Retrieve Contexts<br/>asyncio.gather / aiohttp] ::: evalDeep
        Retrieve --> RagasEval[run_single_eval] ::: evalDeep
        
        RagasEval --> ThreadPool[loop.run_in_executor] ::: evalDeep
        ThreadPool --> SyncRagas[RAGAS evaluate<br/>Synchronous Thread] ::: evalDeep
        SyncRagas --> NestAsync[nest_asyncio applies & runs nested tasks] ::: evalDeep
        
        NestAsync --> LLMCalls[OpenRouter LLM Calls<br/>Faithfulness, Context Recall] ::: evalDeep
        LLMCalls --> ResultNode[Calculate SingleRunMetrics] ::: evalDeep
        
        ResultNode --> LoopRuns
        LoopRuns -- "All Runs Complete" --> Aggregate[Calculate Median/StdDev] ::: evalDeep
        Aggregate --> ReturnResults((Return Proposed Score)) ::: evalDeep
    end

    %% Connections across subgraphs
    SetState --> StateInit
    ReportWriter --> EndRun([End Script]) ::: terminal
    Evaluator -.-> EvalStart
    ReturnResults -.-> Acceptance
```

### Key Workflow Highlights
1. **State Injection:** The system evaluates the baseline exactly once per code update, caching the results heavily to save time. This score acts as the target to beat for all subsequent iterations.
2. **Short-Circuiting Failures:** Nodes like `Validator`, `Deduplicator`, and `SmokeTest` act as inexpensive guardrails. If any fail, the graph skips the expensive `Indexer` and `Evaluator` nodes, immediately routing to `Recorder` to log the failure before passing context to the `Reflection` node.
3. **Evaluator Execution (The recent fix):** In step 3, `run_single_eval` delegates the synchronous RAGAS library to a separate background thread via `loop.run_in_executor`. We removed the forceful `asyncio.wait_for` wrapper so the thread can safely execute nested asynchronous API calls (enabled by `nest_asyncio`) without clashing with the main thread's Windows I/O completion polling. Timeout tracking is natively handled within RAGAS configurations instead.
