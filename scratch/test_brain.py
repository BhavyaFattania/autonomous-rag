# scratch/test_brain.py
import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.loader import load_baseline_config
from dotenv import load_dotenv
from src.scientist.prompt_builder import build_scientist_prompt as _build_scientist_prompt
from src.utils.openrouter import call_openrouter


async def test_brain():
    load_dotenv()

    baseline = load_baseline_config()

    state = {
        "experiments_completed": 15,
        "successful_patterns": [
            "High top_k increases recall",
            "Hierarchical chunking works better for long docs",
        ],
        "failed_patterns": ["BM25 only drops precision", "Alpha=0.0 ignores semantics completely"],
        "baseline_config": baseline,
        "current_best_config": baseline,
        "reflection_summary": "We need to try hybrid search with semantic chunking to balance exact match and context.",
    }

    prompt = _build_scientist_prompt(state, exploit=False)

    messages = [{"role": "user", "content": prompt}]

    print("Sending prompt to OpenRouter...")
    response = await call_openrouter(
        model_id="deepseek/deepseek-v4-pro",  # Note: using v4-pro might be slow/expensive, deepseek/deepseek-chat or qwen/qwen3.5-flash-02-23 could be faster for a test but let's stick to v4-pro as used in brain.py
        messages=messages,
        max_tokens=4000,
        task="scientist",
        reasoning_effort="high",
        temperature=0.7,
        return_reasoning=True,
    )

    artifacts_dir = Path(
        r"C:\Users\BHAVYA\.gemini\antigravity-ide\brain\e113d92a-fdef-4f35-80aa-9315ce93acdf"
    )
    out_file = artifacts_dir / "scientist_io.md"

    with open(out_file, "w", encoding="utf-8") as f:
        f.write("# Scientist Brain: Input and Output\n\n")
        f.write("## Input Prompt\n")
        f.write("```text\n")
        f.write(prompt)
        f.write("\n```\n\n")
        f.write("## Output Response\n")
        f.write("```json\n")
        f.write(json.dumps(response, indent=2))
        f.write("\n```\n")

    print(f"Done. Wrote to {out_file}")


if __name__ == "__main__":
    asyncio.run(test_brain())
