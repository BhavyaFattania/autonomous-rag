# Ruflo Agents Reference Guide

You can use these agent roles when prompting me to spawn specialized Ruflo agents or coordinate swarms.

## Core Agents
* **`coder`**: Implements code, handles refactoring, and fixes bugs.
* **`reviewer`**: Analyzes code quality, logic correctness, and styling.
* **`tester`**: Writes unit, integration, and end-to-end tests.
* **`planner`**: Creates implementation details and schedules execution steps.
* **`researcher`**: Gathers information, reads files, and analyzes the codebase.

## Architecture Agents
* **`system-architect`**: Designs system boundaries, databases, and microservices.
* **`backend-dev`**: Focuses on APIs, backend business logic, and integrations.
* **`mobile-dev`**: Specializes in mobile client applications.

## Security Agents
* **`security-architect`**: Focuses on threat modeling, security architecture, and cryptography.
* **`security-auditor`**: Conducts vulnerability scans and security code reviews.

## Performance Agents
* **`performance-engineer`**: Profiles execution and optimizes database queries or CPU/memory hot-paths.
* **`perf-analyzer`**: Runs benchmark tests and analyzes system latency.

## Coordination Agents
* **`hierarchical-coordinator`**: Manages a traditional tree-based top-down delegation structure.
* **`mesh-coordinator`**: Handles decentralized node-to-node peer communication.
* **`adaptive-coordinator`**: Adjusts swarm topology dynamically based on task load.

## GitHub Agents
* **`pr-manager`**: Automates Pull Request creation, description updates, and branch merges.
* **`code-review-swarm`**: Multi-agent review swarm for validating incoming pull requests.
* **`issue-tracker`**: Manages issue boards and links code commits to bug tickets.
* **`release-manager`**: Automates changelog compilation and release deployments.

---

## WASM Agent Templates
These run in sandboxed WASM environments:
* **`coder`** (Version 1.0.0)
* **`researcher`** (Version 1.0.0)
* **`tester`** (Version 1.0.0)
* **`reviewer`** (Version 1.0.0)
* **`security`** (Version 1.0.0)
* **`swarm-orchestrator`** (Version 1.0.0)
