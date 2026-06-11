# RuFlo Features & Capabilities Reference

RuFlo is a next-generation AI Agent Orchestration Platform designed for high-performance, secure, and self-learning multi-agent collaboration. Below is the comprehensive list of features, categorized by functionality.

---

## 1. Agent Management & Orchestration
Run and orchestrate AI agents for development, research, testing, and more.
* **Specialized Agent Spawning:** Spawn agents matching specific roles (e.g., `coder`, `researcher`, `tester`, `reviewer`).
* **WASM Sandboxed Agents:** Run untrusted code or agents securely in sandboxed WebAssembly environments (`agent wasm-create`).
* **Persistent Autopilot Swarm (`autopilot`):** Keeps swarms working continuously on tasks (e.g., overnight) until all items are verified and completed.
* **Agent Pools:** Scale agent instances dynamically to handle parallel workloads.

## 2. Swarm Coordination Topologies
Coordinate multi-agent teams using advanced routing topologies.
* **Hierarchical Topologies:** Centralized lead-to-subagent task delegation (Standard Pipeline pattern).
* **Mesh Topologies:** Decentralized peer-to-peer communication among agents.
* **Hive-Mind Coordination:** Queen-led, consensus-based agent networks for complex, cooperative decision-making.
* **Anti-Drift Routing:** Ensures agents remain aligned to the main task parameters during multi-step runs.

## 3. Memory & Self-Learning Systems
A hybrid vector database layer that allows agents to remember context and learn over time.
* **AgentDB:** A high-performance storage engine using HNSW (Hierarchical Navigable Small World) indexing for 150x to 12,500x faster recall.
* **Neural Pattern Learning:** Learn and train neural weights on successful trajectories to optimize future task completion (`ruflo neural`).
* **Semantic Search:** Store and query patterns, codes, and project history across namespaces (`ruflo memory search`).
* **Claude/IDE History Bridge:** Automatically import context and past trajectories into local memory.

## 4. Intelligent Workflow Hooks
Automate and route tasks dynamically based on triggers.
* **Self-Learning Router (`hooks route`):** Automatically routes incoming tasks to the most suitable agent using Q-learning.
* **Lifecycle Hooks:** Execute custom logic or diagnostics before/after tasks and commands (`pre-task`, `post-task`, `pre-command`, `post-command`).
* **Worker Dispatching:** Automatically trigger specialized background tasks (e.g., `audit`, `optimize`, `testgaps`) when code changes.

## 5. Security & AI Defense (AIDefence)
Enforce code safety and audit project assets dynamically.
* **Safety Scanner (`aidefence scan`):** Analyze project changes for potential security vulnerabilities and threats.
* **PII Detection:** Detect and redact Personally Identifiable Information (PII) before syncing code or memory.
* **Enforcement Gates (`guidance gates`):** Prevent dangerous commands (e.g., `rm -rf /`) from being run by autonomous agents.

## 6. Guidance Control Plane
Enforce rules, coding guidelines, and custom restrictions.
* **CLAUDE.md Compiler:** Compile human-readable instructions into structured policies (constitution + shards + manifest).
* **Guidance Shard Retrieval:** Automatically load task-relevant shards based on the task description.
* **A/B Policy Testing:** Run behavioral comparison tests between different instruction/guideline sets.

## 7. Analysis & Diagnostics
Understand codebase structure and risk levels before committing code.
* **Diff Risk Assessment (`analyze diff-risk`):** Automatically calculate the complexity and risk level of a diff.
* **Graph Boundaries:** Analyze code boundaries to locate dependencies and potential breakages.
* **Doctor Diagnostics (`ruflo doctor --fix`):** Scan system health, configurations, and API keys, and automatically fix setup issues.

## 8. Decentralized Plugins & Registry
Extend the platform with custom modules.
* **IPFS Plugin Registry:** Search and install community plugins from a decentralized IPFS registry (`ruflo plugins`).
* **Appliance Packager:** Package agents, tools, and configurations into standalone, self-contained RuFlo Appliance (`.rvfa`) files.
