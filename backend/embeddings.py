#!/usr/bin/env python3
# -------------------------------------------------------
# backend/embeddings.py
# -------------------------------------------------------
# Author: projectfong
# Purpose Summary:
#   - Provide 1024-d embeddings via Ollama (snowflake-arctic-embed) or OpenAI fallback.
#   - Deterministically pad/truncate to 1024 if models differ in dimension.
# Audit:
#   - Logs provider used and vector shape with timestamps.
#   - Fails safe: returns zero-vector on hard errors while logging the exception.
# -------------------------------------------------------
import os, json, datetime, math
import requests


def _ts():
    # Audit: ISO8601 with UTC 'Z' suffix
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def _pad_trunc(vec, dim=1024):
    v = list(vec or [])
    if len(v) >= dim:
        return v[:dim]
    return v + [0.0]*(dim - len(v))

def embed_text(text: str) -> list[float]:
    try:
        if os.getenv("OPENAI_API_KEY"):
            # OpenAI path
            from typing import cast
            import requests as rq
            url = "https://api.openai.com/v1/embeddings"
            model = os.getenv("OPENAI_EMBED_MODEL","text-embedding-3-large")
            r = rq.post(url, headers={"Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"}, json={"model": model, "input": text})
            data = r.json()
            vec = data["data"][0]["embedding"]
            out = _pad_trunc(vec, 1024)
            print(f"{_ts()} embeddings.openai model={model} in={len(text)} out=1024")
            return out
        else:
            # Ollama path
            host = os.getenv("OLLAMA_HOST","http://localhost:11434")
            model = os.getenv("OLLAMA_EMBED_MODEL","snowflake-arctic-embed")
            r = requests.post(f"{host}/api/embeddings", json={"model": model, "prompt": text}, timeout=60)
            vec = r.json().get("embedding", [])
            out = _pad_trunc(vec, 1024)
            print(f"{_ts()} embeddings.ollama model={model} in={len(text)} out=1024")
            return out
    except Exception as e:
        print(f"{_ts()} embeddings.error {e}")
        return [0.0]*1024
