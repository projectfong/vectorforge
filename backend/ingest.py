#!/usr/bin/env python3
# -------------------------------------------------------
# backend/ingest.py
# -------------------------------------------------------
# Author: projectfong
# Purpose Summary:
#   - Crawl provided URLs, extract text, summarize via LLM, and upsert:
#       * pgvector: full-text rich embeddings (1024d) for deep semantic search.
#       * qdrant: summary embeddings (1024d) for fast summary retrieval.
#   - Keep original URLs in both stores.
# Audit:
#   - Prints each major step and row counts with timestamps.
#   - Fails safe per document; continues on error and logs it.
# -------------------------------------------------------
import os, re, datetime
import requests
from bs4 import BeautifulSoup
import psycopg2
from qdrant_client import QdrantClient
from qdrant_client.http import models as qm
from embeddings import embed_text
import csv
from io import StringIO

def _ts():
    # Audit: ISO8601 with UTC 'Z' suffix
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


PG_URL = os.getenv("DATABASE_URL")
Q_URL = os.getenv("QDRANT_URL","http://localhost:6333")

def _pg_conn():
    return psycopg2.connect(PG_URL)

def _pg_init():
    with _pg_conn() as c, c.cursor() as cur:
        cur.execute("""
        CREATE EXTENSION IF NOT EXISTS vector;
        CREATE TABLE IF NOT EXISTS space_docs (
            id SERIAL PRIMARY KEY,
            url TEXT UNIQUE,
            title TEXT,
            content TEXT,
            embedding vector(1024)
        );
        """)
        c.commit()
    print(f"{_ts()} ingest.pg init ok" )

def _qd_init():
    qc = QdrantClient(url=Q_URL)
    try:
        qc.create_collection(
            collection_name="space_summaries",
            vectors_config=qm.VectorParams(size=1024, distance=qm.Distance.COSINE),
        )
        print(f"{_ts()} ingest.qdrant created collection space_summaries" )
    except Exception:
        print(f"{_ts()} ingest.qdrant collection exists" )
    return qc

def _html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script","style","noscript"]):
        tag.decompose()
    return re.sub(r"\s+"," ", soup.get_text(separator=" ").strip())

def _summarize(text: str) -> str:
    try:
        # Prefer OpenAI if available, else Ollama
        if os.getenv("OPENAI_API_KEY"):
            import requests as rq
            r = rq.post("https://api.openai.com/v1/chat/completions",
                        headers={"Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"},
                        json={"model": os.getenv("OPENAI_CHAT_MODEL","gpt-4o-mini"),
                              "messages":[{"role":"system","content":"Summarize in 5 concise bullet points with key findings and organism/context."},
                                          {"role":"user","content": text[:6000]}],
                              "temperature": 0.2})
            return r.json()["choices"][0]["message"]["content"]
        else:
            r = requests.post(os.getenv("OLLAMA_HOST","http://localhost:11434") + "/api/chat",
                              json={"model": os.getenv("OLLAMA_CHAT_MODEL","llama3.1:8b-instruct"),
                                    "messages":[{"role":"system","content":"Summarize in 5 concise bullet points with key findings and organism/context."},
                                                {"role":"user","content": text[:6000]}]})
            return r.json().get("message",{}).get("content","")
    except Exception as e:
        print(f"{_ts()} ingest.summarize.error {e}")
        return ""

def ingest_sources(urls: list[str], max_pages: int = 100) -> int:
    _pg_init()
    qc = _qd_init()
    inserted = 0
    for i, url in enumerate(urls[:max_pages]):
        try:
            print(f"{_ts()} ingest.fetch {url}")
            resp = requests.get(url, timeout=60)
            txt = _html_to_text(resp.text)
            title = (txt[:80] + "...") if len(txt) > 83 else txt
            emb = embed_text(txt[:8000])
            summ = _summarize(txt[:8000])
            s_emb = embed_text(summ or txt[:2000])

            # pg upsert
            with _pg_conn() as c, c.cursor() as cur:
                cur.execute("""
                INSERT INTO space_docs (url,title,content,embedding)
                VALUES (%s,%s,%s,%s)
                ON CONFLICT (url) DO UPDATE SET
                  title=EXCLUDED.title, content=EXCLUDED.content, embedding=EXCLUDED.embedding
                """, (url, title, txt, emb))
                c.commit()

            # qdrant upsert
            qc.upsert(collection_name="space_summaries",
                      points=[qm.PointStruct(id=abs(hash(url)) % (2**63),
                                             vector=s_emb,
                                             payload={"url": url, "title": title, "summary": summ})])
            inserted += 1
            print(f"{_ts()} ingest.ok url={url} len={len(txt)}" )
        except Exception as e:
            print(f"{_ts()} ingest.error url={url} err={e}")
            continue
    print(f"{_ts()} ingest.done count={inserted}")
    return inserted

def ingest_spacebio_csv(csv_url: str, limit: int = 50) -> int:
    _pg_init()
    qc = _qd_init()
    print(f"{_ts()} ingest.csv fetch {csv_url}")

    # --- Normalize encoding and detect delimiter dynamically ---
    resp = requests.get(csv_url, timeout=60)
    content = resp.content.decode('utf-8-sig').replace("\r\n", "\n")
    sample = content.splitlines()[0]
    delimiter = ';' if ';' in sample else ','
    reader = csv.DictReader(StringIO(content), delimiter=delimiter)
    print(f"{_ts()} ingest.csv headers={reader.fieldnames} delimiter={delimiter!r}")

    count = 0
    for i, row in enumerate(reader):
        if i >= limit:
            break
        try:
            title = (
                row.get("Title")
                or row.get("title")
                or row.get("TITLE")
                or "Untitled"
            )
            link = (
                row.get("URL")
                or row.get("url")
                or row.get("Link")
                or row.get("link")
                or ""
            )
            abstract = (
                row.get("Abstract")
                or row.get("abstract")
                or row.get("ABSTRACT")
                or ""
            )
            if not link:
                continue

            text = f"{title}\n\n{abstract}"
            emb = embed_text(text)
            summ = _summarize(text)
            s_emb = embed_text(summ or text[:2000])

            # --- pgvector upsert ---
            with _pg_conn() as c, c.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO space_docs (url, title, content, embedding)
                    VALUES (%s,%s,%s,%s)
                    ON CONFLICT (url) DO UPDATE SET
                        title=EXCLUDED.title,
                        content=EXCLUDED.content,
                        embedding=EXCLUDED.embedding
                    """,
                    (link, title, abstract, emb),
                )
                c.commit()

            # --- Qdrant upsert ---
            qc.upsert(
                collection_name="space_summaries",
                points=[
                    qm.PointStruct(
                        id=abs(hash(link)) % (2**63),
                        vector=s_emb,
                        payload={
                            "url": link,
                            "title": title,
                            "summary": summ,
                        },
                    )
                ],
            )
            count += 1
            print(f"{_ts()} ingest.csv ok {i+1}: {title[:60]}...")
        except Exception as e:
            print(f"{_ts()} ingest.csv error row={i} err={e}")
            continue

    print(f"{_ts()} ingest.csv done count={count}")
    return count
