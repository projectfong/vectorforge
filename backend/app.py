#!/usr/bin/env python3
# -------------------------------------------------------
# backend/app.py
# -------------------------------------------------------
# Author: projectfong
# Purpose Summary:
#   - FastAPI gateway exposing /api/ingest, /api/search, /api/summarize.
#   - Orchestrates hybrid search across pgvector (rich) and qdrant (summaries).
#   - Routes queries by intent keywords (summary/summarize -> qdrant else pgvector).
# Audit:
#   - All requests and key actions are printed with ISO8601 UTC timestamps.
#   - Fail-safe: any exception returns 500 with error logged; no secrets printed.
# -------------------------------------------------------

import os, json, datetime
from fastapi import FastAPI, Query
from pydantic import BaseModel
from dotenv import load_dotenv
from orchestrator import Orchestrator
from ingest import ingest_sources
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI(title="SpaceBio Knowledge Engine API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _ts():
    # Audit: ISO8601 with UTC 'Z' suffix
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


ORCH = Orchestrator()

class IngestBody(BaseModel):
    urls: list[str] = []
    max_pages: int = 100

class SearchBody(BaseModel):
    query: str
    topk: int | None = None
    hybrid: bool = True

@app.post("/api/ingest")
def api_ingest(body: IngestBody):
    print(f"{_ts()} app.api_ingest start urls={len(body.urls)} max_pages={body.max_pages}")
    count = ingest_sources(body.urls, body.max_pages)
    print(f"{_ts()} app.api_ingest done inserted={count}")
    return {"inserted": count}

@app.post("/api/ingest_csv")
def api_ingest_csv():
    url = "https://raw.githubusercontent.com/jgalazka/SB_publications/main/SB_publication_PMC.csv"
    print(f"{_ts()} app.api_ingest_csv start {url}")
    from ingest import ingest_spacebio_csv
    count = ingest_spacebio_csv(url, limit=50)
    print(f"{_ts()} app.api_ingest_csv done inserted={count}")
    return {"inserted": count}

@app.post("/api/search")
def api_search(body: SearchBody):
    print(f"{_ts()} app.api_search start query={body.query!r} topk={body.topk} hybrid={body.hybrid}")
    res = ORCH.search(body.query, topk=body.topk or int(os.getenv("DEFAULT_TOPK","10")), hybrid=body.hybrid)
    print(f"{_ts()} app.api_search done results={len(res.get('results', []))}")
    return res

@app.get("/healthz")
def healthz():
    return {"ok": True, "time": _ts()}

if __name__ == "__main__":
    import uvicorn
    print(f"{_ts()} app.main starting uvicorn :8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
