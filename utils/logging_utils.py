import json as _json
from datetime import datetime as _dt, timezone
from pathlib import Path
import uuid as _uuid

LLM_LOG_DIR = "output/llm_metadata"
LLM_MODEL_PRICING = {
    "gpt-4o-mini": {"input": 0.0005, "output": 0.0015},  # $/1K tokens
    # Add more models and their pricing as needed
}

def log_llm_metadata(provider, model, messages, response, elapsed, prompt_tokens, completion_tokens):
    now = _dt.now(timezone.utc).isoformat().replace("+00:00", "Z")
    log = {
        "timestamp": now,
        "provider": provider,
        "model": model,
        "messages": messages,
        "response": response,
        "elapsed_seconds": elapsed,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
    }
    # Estimate cost if pricing info is available
    pricing = LLM_MODEL_PRICING.get(model)
    if pricing:
        log["estimated_cost_usd"] = (
            (prompt_tokens / 1000) * pricing["input"] +
            (completion_tokens / 1000) * pricing["output"]
        )
    else:
        log["estimated_cost_usd"] = None
    # Prepare output directory structure: output/llm_metadata/{provider}/{model}/
    out_dir = Path(LLM_LOG_DIR) / provider / model
    out_dir.mkdir(parents=True, exist_ok=True)
    fname = out_dir / f"llm_{now.replace(':', '').replace('.', '')}_{_uuid.uuid4().hex[:8]}.json"
    try:
        with open(fname, "w") as f:
            _json.dump(log, f, indent=2)
    except Exception as e:
        print(f"Failed to write LLM metadata log: {e}") 