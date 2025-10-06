#!/usr/bin/env python3
# -------------------------------------------------------
# backend/orchestrator.py
# -------------------------------------------------------
# Author: projectfong
# Purpose Summary:
#   - Hybrid search orchestrator across pgvector and qdrant.
#   - Routing: if query contains 'summary' or 'summarize' -> prioritize qdrant.
#   - Otherwise pgvector semantic search with optional keyword filter.
# Audit:
#   - Logs routing decisions and query params with timestamps.
#   - Fails safe: returns empty result list on error with error logged.
# -------------------------------------------------------
import os, re, datetime
import psycopg2
from embeddings import embed_text
from qdrant_client import QdrantClient
from qdrant_client.http import models as qm


def _ts():
    # Audit: ISO8601 with UTC 'Z' suffix
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


class Orchestrator:
    def __init__(self):
        self.pg_url = os.getenv("DATABASE_URL")
        self.q_url = os.getenv("QDRANT_URL","http://localhost:6333")
        self.qc = QdrantClient(url=self.q_url)

    def _pg(self):
        return psycopg2.connect(self.pg_url)

    def _pg_search(self, query: str, topk: int, keyword: str | None):
        emb = embed_text(query)
        sql = """
        SELECT url, title, content, 1 - (embedding <=> %s::vector) AS score
        FROM space_docs
        {kw}
        ORDER BY embedding <=> %s::vector
        LIMIT %s
        """
        kw_clause = ""
        args = [emb]
        if keyword:
            kw_clause = "WHERE (title ILIKE %s OR content ILIKE %s)"
            args.extend([f"%{keyword}%", f"%{keyword}%"])
        args.extend([emb, topk])
        with self._pg() as c, c.cursor() as cur:
            cur.execute(sql.format(kw=kw_clause), args)
            rows = cur.fetchall()
        return [{"source":"pgvector","url":r[0],"title":r[1],"snippet":(r[2][:240] + "..."),"score":float(r[3])} for r in rows]

    def _qd_search(self, query: str, topk: int):
        emb = embed_text(query)
        res = self.qc.search(collection_name="space_summaries", query_vector=emb, limit=topk, with_payload=True)
        out = []
        for p in res:
            pl = p.payload or {}
            out.append({"source":"qdrant","url":pl.get("url"),"title":pl.get("title"),"summary":pl.get("summary"),"score":float(p.score)})
        return out

    def search(self, query: str, topk: int = 10, hybrid: bool = True):
        try:
            keyword = None
            if ":" in query:
                # simple keyword filter syntax: kw:foo rest of query
                m = re.search(r"kw:(\w+)", query)
                if m:
                    keyword = m.group(1)
            route_qd = any(k in query.lower() for k in ["summary","summarize","overview"])
            print(f"{_ts()} orchestrator.route route_qd={route_qd} hybrid={hybrid} kw={keyword}")
            qd = self._qd_search(query, topk) if (route_qd or hybrid) else []
            pg = self._pg_search(query, topk, keyword) if (not route_qd or hybrid) else []
            results = sorted(qd + pg, key=lambda x: x.get("score",0), reverse=True)[:topk]
            return {"query": query, "results": results, "routed": "qdrant" if route_qd else "pgvector", "hybrid": hybrid}
        except Exception as e:
            print(f"{_ts()} orchestrator.error {e}")
            return {"query": query, "results": [], "error": str(e)}
