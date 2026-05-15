#!/bin/bash
set -e

echo "=== RAG Optimizer Environment Setup ==="

# 1. Check Python version
python3 --version | grep -q "3.11" || (echo "ERROR: Python 3.11 required" && exit 1)
echo "[OK] Python 3.11"

# 2. Install Poetry if not present
command -v poetry &>/dev/null || pip install poetry==1.8.3
echo "[OK] Poetry"

# 3. Install dependencies
poetry install
echo "[OK] Dependencies installed"

# 4. Create .env if not exists
if [ ! -f .env ]; then
    cp .env.example .env
    echo "[INFO] .env created from .env.example. Fill in your API keys."
fi

# 5. Start Qdrant via Docker (local dev)
docker compose up -d qdrant
echo "[OK] Qdrant started"

# 6. Create required directories
mkdir -p data/hotpotqa data/corpus logs reports prompts
echo "[OK] Directories created"

echo ""
echo "Next steps:"
echo "  1. Fill in OPENROUTER_API_KEY in .env"
echo "  2. Run: python data/hotpotqa/setup_hotpotqa.py"
echo "  3. Run: python scripts/run_overnight.py --dry-run"
echo "  4. Run: python scripts/run_overnight.py --max-exp 3 --max-hours 1  (smoke test)"
