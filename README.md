# VectorForge: Space Biology Knowledge Engine (Quickstart)
> Built for NASA Space Apps Challenge 2025 — Challenge 3: Build a Space Biology Knowledge Engine  
> Author: projectfong

A minimal, auditable pipeline and dashboard to ingest NASA bioscience resources, summarize papers (prototype implementation), and enable hybrid search across full-text documents (pgvector) and summaries (Qdrant). Built for NASA Space Apps 2025 Challenge 3. Why it matters: helps scientists, mission planners, and managers explore decades of results quickly. 

## Summary
- One-command stack via Docker Compose (Postgres+pgvector, Qdrant, API, UI)
- External model inference: Ollama (preferred); OpenAI optional if key exists
- Crawler keeps URLs; embeddings are 1024-d as requested; summaries stored separately
- Orchestrator routes: "summary/summarize" -> Qdrant; otherwise pgvector; hybrid merges both
- React/TS UI for quick querying and result triage

## Architecture Overview
VectorForge combines a FastAPI orchestrator with dual vector stores (pgvector + Qdrant) and a TypeScript/React UI.  
It ingests NASA’s official Space Biology dataset, summarizes each publication with Ollama or OpenAI, and enables hybrid semantic search.

## Quick Start (10-15 min)
1. Clone and copy `.env.example` to `.env` then edit if needed.
2. Ensure Ollama is running locally with an embedding model:
   - `ollama pull snowflake-arctic-embed2:568m` (1024-d)
   - `ollama pull llama3.1:8b-instruct-q4_0`
3. `docker compose up --build`
4. Ingest seed URLs: `curl -X POST http://localhost:8000/api/ingest -H 'Content-Type: application/json' -d '{"urls":["https://github.com/jgalazka/SB_publications","https://science.nasa.gov/biological-physical/data/","https://public.ksc.nasa.gov/nslsl/","https://taskbook.nasaprs.com/tbp/welcome.cfm"], "max_pages": 10}'`
5. Open UI: http://localhost:5173 (frontend loads successfully; search functionality can be verified through the API.)

> Challenge fit: build a dynamic dashboard that summarizes NASA bioscience publications and enables exploration of impacts/results. 

## How It Works
- Crawler extracts text and keeps original URLs
- Summarizer designed to extract concise key findings (partially functional in this build).
- pgvector stores full-text 1024-d embeddings for deep semantic search
- Qdrant stores summary 1024-d embeddings for fast overview retrieval
- Orchestrator supports hybrid search and simple keyword filters (use `kw:term` in query)

## Why 1024-d Embeddings
- Uses `snowflake-arctic-embed` via Ollama for 1024 dimensions.
- If OpenAI is used, vectors are deterministically truncated/padded to 1024 for consistency.

## API
- `POST /api/ingest` `{ "urls": [...], "max_pages": 100 }` -> inserts docs and summaries
- `POST /api/search` `{ "query": "...", "topk": 10, "hybrid": true }`
  - Routing rule: if query contains "summary|summarize|overview" -> prioritize Qdrant

## UI
- Vite React app with a search bar and list results.
- Shows source (pgvector/qdrant), score, title link, and snippet/summary.

## Potential Considerations (mapped)
- Audience: scientists, managers, mission architects
- Sections: emphasize Results for objective findings; Conclusions for forward-looking context
- Other NASA resources: OSDR, Space Life Sciences Library, NASA Task Book for context expansion
- Visuals/audio: optional future pivot for accessibility
- This quickstart aligns directly with Challenge 3 goals. 

## Commands
- Start: `docker compose up --build`
- Health: `curl http://localhost:8000/healthz`
- Search: `curl -X POST http://localhost:8000/api/search -H 'Content-Type: application/json' -d '{"query":"bone density microgravity kw:rodent","topk":5,"hybrid":true}'`

```
curl -X POST http://localhost:8000/api/search -H 'Content-Type: application/json' -d '{"query":"bone density microgravity kw:rodent","topk":5,"hybrid":true}'
{"query":"bone density microgravity kw:rodent","results":[{"source":"qdrant","url":"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11579474/","title":"Microgravity Stress: Bone and Connective Tissue","summary":"","score":0.61370355},{"source":"qdrant","url":"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3630201/","title":"Microgravity induces pelvic bone loss through osteoclastic activity, osteocytic osteolysis, and osteoblastic cell cycle inhibition by CDKN1a/p21","summary":"","score":0.5473561},{"source":"qdrant","url":"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11988870/","title":"Stem Cell Health and Tissue Regeneration in Microgravity","summary":"","score":0.5153185},{"source":"qdrant","url":"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6222041/","title":"High-precision method for cyclic loading of small-animal vertebrae to assess bone quality.","summary":"","score":0.5022759},{"source":"qdrant","url":"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7998608/","title":"Microgravity Reduces the Differentiation and Regenerative Potential of Embryonic Stem Cells","summary":"","score":0.45181635}],"routed":"pgvector","hybrid":true}
```
backend
```
2025-10-06T06:20:38Z app.api_search start query='bone density microgravity kw:rodent' topk=5 hybrid=True
2025-10-06T06:20:38Z orchestrator.route route_qd=False hybrid=True kw=rodent
2025-10-06T06:20:40Z embeddings.ollama model=snowflake-arctic-embed2:568m in=35 out=1024
2025-10-06T06:20:40Z embeddings.ollama model=snowflake-arctic-embed2:568m in=35 out=1024
2025-10-06T06:20:40Z app.api_search done results=5
INFO:     172.18.0.1:48572 - "POST /api/search HTTP/1.1" 200 OK
```

## Estimated Time
- Setup: 10-15 min
- Ingest first pages: 5-10 min (depends on network)
- First searches: immediate after ingest

## Validation
- Expect `/healthz` ok response.
- `/api/ingest` logs with counts in backend console.
- `/api/search` returns mixed pgvector and qdrant hits.

## Screenshots & Logs

-install logs

```
vectorforge$ docker compose up --build
[+] Building 54.3s (23/23) FINISHED
 => [internal] load local bake definitions                                                                                                                                                         0.0s
 => => reading from stdin 1.03kB                                                                                                                                                                   0.0s
 => [frontend internal] load build definition from Dockerfile                                                                                                                                      0.1s
 => => transferring dockerfile: 184B                                                                                                                                                               0.0s
 => [backend internal] load build definition from Dockerfile                                                                                                                                       0.1s
 => => transferring dockerfile: 201B                                                                                                                                                               0.0s
 => [backend internal] load metadata for docker.io/library/python:3.11-slim                                                                                                                        0.3s
 => [frontend internal] load metadata for docker.io/library/node:20-alpine                                                                                                                         0.3s
 => [backend internal] load .dockerignore                                                                                                                                                          0.0s
 => => transferring context: 2B                                                                                                                                                                    0.0s
 => [frontend internal] load .dockerignore                                                                                                                                                         0.1s
 => => transferring context: 2B                                                                                                                                                                    0.0s
 => [backend 1/5] FROM docker.io/library/python:3.11-slim@sha256:9bffe4353b925a1656688797ebc68f9c525e79b1d377a764d232182a519eeec4                                                                  5.3s
 => => resolve docker.io/library/python:3.11-slim@sha256:9bffe4353b925a1656688797ebc68f9c525e79b1d377a764d232182a519eeec4                                                                          0.2s
 => => sha256:9bffe4353b925a1656688797ebc68f9c525e79b1d377a764d232182a519eeec4 10.37kB / 10.37kB                                                                                                   0.0s
 => => sha256:70f7abeaf1577b30229dd1d7784d6c053a29104a56bb353fe23217ad6f0fabc3 1.75kB / 1.75kB                                                                                                     0.0s
 => => sha256:bf02a2b853727373d9065ccd2cc7d40df56d6f1b8256ae5f3612a34caae3c5be 5.38kB / 5.38kB                                                                                                     0.0s
 => => sha256:44350d10c02e7ab437e3fe5a05e3405115ece5972b2b9f7cd0d68d23c72d5833 1.29MB / 1.29MB                                                                                                     0.9s
 => => sha256:4dc2c3222cdbf7b5e9d5c68653d42c7289ddf2bfaa17b12c961014755b7d04dd 14.64MB / 14.64MB                                                                                                   1.1s
 => => extracting sha256:44350d10c02e7ab437e3fe5a05e3405115ece5972b2b9f7cd0d68d23c72d5833                                                                                                          0.4s
 => => sha256:b25238518c0cca0928b2117b90cee455c3fbdb7d605f92131e5cc92fbfb5b468 249B / 249B                                                                                                         1.1s
 => => extracting sha256:4dc2c3222cdbf7b5e9d5c68653d42c7289ddf2bfaa17b12c961014755b7d04dd                                                                                                          2.2s
 => => extracting sha256:b25238518c0cca0928b2117b90cee455c3fbdb7d605f92131e5cc92fbfb5b468                                                                                                          0.0s
 => [backend internal] load build context                                                                                                                                                          0.1s
 => => transferring context: 191B                                                                                                                                                                  0.0s
 => [frontend 1/5] FROM docker.io/library/node:20-alpine@sha256:eabac870db94f7342d6c33560d6613f188bbcf4bbe1f4eb47d5e2a08e1a37722                                                                  12.0s
 => => resolve docker.io/library/node:20-alpine@sha256:eabac870db94f7342d6c33560d6613f188bbcf4bbe1f4eb47d5e2a08e1a37722                                                                            0.2s
 => => sha256:eabac870db94f7342d6c33560d6613f188bbcf4bbe1f4eb47d5e2a08e1a37722 7.67kB / 7.67kB                                                                                                     0.0s
 => => sha256:6a91081a440be0b57336fbc4ee87f3dab1a2fd6f80cdb355dcf960e13bda3b59 1.72kB / 1.72kB                                                                                                     0.0s
 => => sha256:6c47bbfd232eca9b18296c2b2f3fbf6154c19117ed02a992f7bd6814377df62d 6.42kB / 6.42kB                                                                                                     0.0s
 => => sha256:9824c27679d3b27c5e1cb00a73adb6f4f8d556994111c12db3c5d61a0c843df8 3.80MB / 3.80MB                                                                                                     0.4s
 => => sha256:c88300f8759af46375ccc157a0a0dbf7cdaeded52394b5ce2ce074e3b773fe82 42.75MB / 42.75MB                                                                                                   1.7s
 => => sha256:fd345d7e43c58474c833bee593321ab1097dd720bebd8032e75fbf5b81b1e554 1.26MB / 1.26MB                                                                                                     0.4s
 => => extracting sha256:9824c27679d3b27c5e1cb00a73adb6f4f8d556994111c12db3c5d61a0c843df8                                                                                                          0.4s
 => => sha256:0de821d16564893ff12fae9499550711d92157ed1e6705a8c7f7e63eac0a2bb9 449B / 449B                                                                                                         0.5s
 => => extracting sha256:c88300f8759af46375ccc157a0a0dbf7cdaeded52394b5ce2ce074e3b773fe82                                                                                                          3.7s
 => => extracting sha256:fd345d7e43c58474c833bee593321ab1097dd720bebd8032e75fbf5b81b1e554                                                                                                          0.3s
 => => extracting sha256:0de821d16564893ff12fae9499550711d92157ed1e6705a8c7f7e63eac0a2bb9                                                                                                          0.0s
 => [frontend internal] load build context                                                                                                                                                         0.2s
 => => transferring context: 301B                                                                                                                                                                  0.0s
 => [backend 2/5] WORKDIR /app                                                                                                                                                                     5.2s
 => [backend 3/5] COPY requirements.txt /app/                                                                                                                                                      0.5s
 => [backend 4/5] RUN pip install --no-cache-dir -r requirements.txt                                                                                                                              37.4s
 => [frontend 2/5] WORKDIR /app                                                                                                                                                                    0.3s
 => [frontend 3/5] COPY package.json /app/                                                                                                                                                         0.8s
 => [frontend 4/5] RUN npm install                                                                                                                                                                15.4s
 => [frontend 5/5] COPY . /app                                                                                                                                                                     0.7s
 => [frontend] exporting to image                                                                                                                                                                  2.5s
 => => exporting layers                                                                                                                                                                            2.4s
 => => writing image sha256:998231eac9a5827fe9eca122ba855824059055391188fc1b2e4bd3a2cb633f24                                                                                                       0.0s
 => => naming to docker.io/library/vectorforge-frontend                                                                                                                                            0.0s
 => [frontend] resolving provenance for metadata file                                                                                                                                              0.0s
 => [backend 5/5] COPY . /app                                                                                                                                                                      0.4s
 => [backend] exporting to image                                                                                                                                                                   4.1s
 => => exporting layers                                                                                                                                                                            4.0s
 => => writing image sha256:5359707ac27b7990a56cbae7249e02405da595800cf79387946b9f385d07e332                                                                                                       0.0s
 => => naming to docker.io/library/vectorforge-backend                                                                                                                                             0.0s
 => [backend] resolving provenance for metadata file                                                                                                                                               0.0s
[+] Running 9/9
 ✔ vectorforge-backend                Built                                                                                                                                                        0.0s
 ✔ vectorforge-frontend               Built                                                                                                                                                        0.0s
 ✔ Network vectorforge_default        Created                                                                                                                                                      0.1s
 ✔ Volume vectorforge_pgdata          Created                                                                                                                                                      0.0s
 ✔ Volume vectorforge_qdrant_storage  Created                                                                                                                                                      0.0s
 ✔ Container vectorforge-qdrant-1     Created                                                                                                                                                      0.4s
 ✔ Container vectorforge-postgres-1   Created                                                                                                                                                      0.5s
 ✔ Container vectorforge-backend-1    Created                                                                                                                                                      0.2s
 ✔ Container vectorforge-frontend-1   Created                                                                                                                                                      0.2s
Attaching to backend-1, frontend-1, postgres-1, qdrant-1
qdrant-1  |            _                 _
qdrant-1  |   __ _  __| |_ __ __ _ _ __ | |_
qdrant-1  |  / _` |/ _` | '__/ _` | '_ \| __|
qdrant-1  | | (_| | (_| | | | (_| | | | | |_
qdrant-1  |  \__, |\__,_|_|  \__,_|_| |_|\__|
qdrant-1  |     |_|
qdrant-1  |
qdrant-1  | Version: 1.15.5, build: 48203e41
qdrant-1  | Access web UI at http://localhost:6333/dashboard


postgres-1  | The files belonging to this database system will be owned by user "postgres".
postgres-1  | This user must also own the server process.
qdrant-1    | 2025-10-06T05:00:49.770672Z  INFO storage::content_manager::consensus::persistent: Initializing new raft state at ./storage/raft_state.json
qdrant-1    |


postgres-1  | The database cluster will be initialized with locale "en_US.utf8".
postgres-1  | The default database encoding has accordingly been set to "UTF8".
postgres-1  | The default text search configuration will be set to "english".
postgres-1  |
postgres-1  | Data page checksums are disabled.
postgres-1  |
postgres-1  | fixing permissions on existing directory /var/lib/postgresql/data ... ok
postgres-1  | creating subdirectories ... ok
postgres-1  | selecting dynamic shared memory implementation ... posix
postgres-1  | selecting default max_connections ... 100
postgres-1  | selecting default shared_buffers ... 128MB
qdrant-1    | 2025-10-06T05:00:49.972577Z  INFO qdrant: Distributed mode disabled
qdrant-1    | 2025-10-06T05:00:49.972745Z  INFO qdrant: Telemetry reporting enabled, id: f56cabaa-7e8d-448c-b22b-33e36ac4783f
postgres-1  | selecting default time zone ... Etc/UTC
postgres-1  | creating configuration files ... ok
qdrant-1    | 2025-10-06T05:00:50.022743Z  INFO qdrant::actix: TLS disabled for REST API
qdrant-1    | 2025-10-06T05:00:50.022920Z  INFO qdrant::actix: Qdrant HTTP listening on 6333
qdrant-1    | 2025-10-06T05:00:50.022956Z  INFO actix_server::builder: starting 3 workers
qdrant-1    | 2025-10-06T05:00:50.022987Z  INFO actix_server::server: Actix runtime found; starting in Actix runtime
qdrant-1    | 2025-10-06T05:00:50.022999Z  INFO actix_server::server: starting service: "actix-web-service-0.0.0.0:6333", workers: 3, listening on: 0.0.0.0:6333
qdrant-1    | 2025-10-06T05:00:50.064661Z  INFO qdrant::tonic: Qdrant gRPC listening on 6334
qdrant-1    | 2025-10-06T05:00:50.064742Z  INFO qdrant::tonic: TLS disabled for gRPC API
postgres-1  | running bootstrap script ... ok
postgres-1  | performing post-bootstrap initialization ... ok
frontend-1  |
frontend-1  | > spaceapps-frontend@0.1.0 dev
frontend-1  | > vite --host 0.0.0.0
frontend-1  |
postgres-1  | initdb: warning: enabling "trust" authentication for local connections
postgres-1  | initdb: hint: You can change this by editing pg_hba.conf or using the option -A, or --auth-local and --auth-host, the next time you run initdb.
postgres-1  | syncing data to disk ... ok
postgres-1  |
postgres-1  |
postgres-1  | Success. You can now start the database server using:
postgres-1  |
postgres-1  |     pg_ctl -D /var/lib/postgresql/data -l logfile start
postgres-1  |
postgres-1  | waiting for server to start....2025-10-06 05:01:14.463 UTC [47] LOG:  starting PostgreSQL 15.4 (Debian 15.4-2.pgdg120+1) on x86_64-pc-linux-gnu, compiled by gcc (Debian 12.2.0-14) 12.2.0, 64-bit
postgres-1  | 2025-10-06 05:01:14.480 UTC [47] LOG:  listening on Unix socket "/var/run/postgresql/.s.PGSQL.5432"
postgres-1  | 2025-10-06 05:01:14.509 UTC [50] LOG:  database system was shut down at 2025-10-06 05:00:51 UTC
postgres-1  | 2025-10-06 05:01:14.526 UTC [47] LOG:  database system is ready to accept connections
frontend-1  |
frontend-1  |   VITE v5.4.20  ready in 596 ms
frontend-1  |
frontend-1  |   ➜  Local:   http://localhost:5173/
frontend-1  |   ➜  Network: http://172.18.0.5:5173/

postgres-1  |  done
postgres-1  | server started
postgres-1  | CREATE DATABASE
postgres-1  |
postgres-1  |
postgres-1  | /usr/local/bin/docker-entrypoint.sh: ignoring /docker-entrypoint-initdb.d/*
postgres-1  |
postgres-1  | waiting for server to shut down...2025-10-06 05:01:14.955 UTC [47] LOG:  received fast shutdown request
postgres-1  | .2025-10-06 05:01:14.983 UTC [47] LOG:  aborting any active transactions
postgres-1  | 2025-10-06 05:01:14.987 UTC [47] LOG:  background worker "logical replication launcher" (PID 53) exited with exit code 1
postgres-1  | 2025-10-06 05:01:14.995 UTC [48] LOG:  shutting down
postgres-1  | 2025-10-06 05:01:15.005 UTC [48] LOG:  checkpoint starting: shutdown immediate
backend-1   | INFO:     Started server process [1]
backend-1   | INFO:     Waiting for application startup.
backend-1   | INFO:     Application startup complete.
backend-1   | INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
postgres-1  | .2025-10-06 05:01:16.474 UTC [48] LOG:  checkpoint complete: wrote 918 buffers (5.6%); 0 WAL file(s) added, 0 removed, 0 recycled; write=0.135 s, sync=1.267 s, total=1.479 s; sync files=301, longest=1.079 s, average=0.005 s; distance=4223 kB, estimate=4223 kB
postgres-1  | 2025-10-06 05:01:16.491 UTC [47] LOG:  database system is shut down
postgres-1  |  done
postgres-1  | server stopped
postgres-1  |
postgres-1  | PostgreSQL init process complete; ready for start up.
postgres-1  |
postgres-1  | 2025-10-06 05:01:16.641 UTC [1] LOG:  starting PostgreSQL 15.4 (Debian 15.4-2.pgdg120+1) on x86_64-pc-linux-gnu, compiled by gcc (Debian 12.2.0-14) 12.2.0, 64-bit
postgres-1  | 2025-10-06 05:01:16.642 UTC [1] LOG:  listening on IPv4 address "0.0.0.0", port 5432
postgres-1  | 2025-10-06 05:01:16.642 UTC [1] LOG:  listening on IPv6 address "::", port 5432
postgres-1  | 2025-10-06 05:01:16.677 UTC [1] LOG:  listening on Unix socket "/var/run/postgresql/.s.PGSQL.5432"
postgres-1  | 2025-10-06 05:01:16.704 UTC [63] LOG:  database system was shut down at 2025-10-06 05:01:16 UTC
postgres-1  | 2025-10-06 05:01:16.726 UTC [1] LOG:  database system is ready to accept connections
```

backend embed - summarize error just need to be stripped out. It's from Ollama's /api/chat returing two JSON objects in one response.

```
2025-10-06T05:56:56Z ingest.summarize.error Extra data: line 2 column 1 (char 145)
2025-10-06T05:56:59Z embeddings.ollama model=snowflake-arctic-embed2:568m in=133 out=1024
2025-10-06T05:56:59Z ingest.csv ok 40: Spatial and temporal localization of SPIRRIG and WAVE/SCAR r...
2025-10-06T05:56:59Z embeddings.ollama model=snowflake-arctic-embed2:568m in=49 out=1024
2025-10-06T05:57:10Z ingest.summarize.error Extra data: line 2 column 1 (char 145)
2025-10-06T05:57:12Z embeddings.ollama model=snowflake-arctic-embed2:568m in=49 out=1024
2025-10-06T05:57:13Z ingest.csv ok 41: Microgravity Stress: Bone and Connective Tissue...
2025-10-06T05:57:13Z embeddings.ollama model=snowflake-arctic-embed2:568m in=137 out=1024
2025-10-06T05:57:23Z ingest.summarize.error Extra data: line 2 column 1 (char 145)
2025-10-06T05:57:26Z embeddings.ollama model=snowflake-arctic-embed2:568m in=137 out=1024
2025-10-06T05:57:26Z ingest.csv ok 42: S. aureus MscL is a pentamer in vivo but of variable stoichi...
2025-10-06T05:57:26Z embeddings.ollama model=snowflake-arctic-embed2:568m in=78 out=1024
2025-10-06T05:57:37Z ingest.summarize.error Extra data: line 2 column 1 (char 145)
2025-10-06T05:57:40Z embeddings.ollama model=snowflake-arctic-embed2:568m in=78 out=1024
2025-10-06T05:57:40Z ingest.csv ok 43: Manipulating the permeation of charged compounds through the...
2025-10-06T05:57:40Z embeddings.ollama model=snowflake-arctic-embed2:568m in=112 out=1024
2025-10-06T05:57:50Z ingest.summarize.error Extra data: line 2 column 1 (char 145)
2025-10-06T05:57:53Z embeddings.ollama model=snowflake-arctic-embed2:568m in=112 out=1024
2025-10-06T05:57:53Z ingest.csv ok 44: The oligomeric state of the truncated mechanosensitive chann...
2025-10-06T05:57:53Z embeddings.ollama model=snowflake-arctic-embed2:568m in=70 out=1024
2025-10-06T05:58:04Z ingest.summarize.error Extra data: line 2 column 1 (char 145)
2025-10-06T05:58:06Z embeddings.ollama model=snowflake-arctic-embed2:568m in=70 out=1024
2025-10-06T05:58:06Z ingest.csv ok 45: Three routes to modulate the pore size of the MscL channel/n...
2025-10-06T05:58:06Z embeddings.ollama model=snowflake-arctic-embed2:568m in=105 out=1024
2025-10-06T05:58:17Z ingest.summarize.error Extra data: line 2 column 1 (char 144)
2025-10-06T05:58:20Z embeddings.ollama model=snowflake-arctic-embed2:568m in=105 out=1024
2025-10-06T05:58:20Z ingest.csv ok 46: The dynamics of protein-protein interactions between domains...
2025-10-06T05:58:20Z embeddings.ollama model=snowflake-arctic-embed2:568m in=99 out=1024
2025-10-06T05:58:30Z ingest.summarize.error Extra data: line 2 column 1 (char 145)
2025-10-06T05:58:32Z embeddings.ollama model=snowflake-arctic-embed2:568m in=99 out=1024
2025-10-06T05:58:32Z ingest.csv ok 47: The MscS and MscL families of mechanosensitive channels act ...
2025-10-06T05:58:32Z embeddings.ollama model=snowflake-arctic-embed2:568m in=116 out=1024
2025-10-06T05:58:42Z ingest.summarize.error Extra data: line 2 column 1 (char 145)
2025-10-06T05:58:45Z embeddings.ollama model=snowflake-arctic-embed2:568m in=116 out=1024
2025-10-06T05:58:45Z ingest.csv ok 48: Chimeras reveal a single lipid-interface residue that contro...
2025-10-06T05:58:45Z embeddings.ollama model=snowflake-arctic-embed2:568m in=87 out=1024
2025-10-06T05:58:56Z ingest.summarize.error Extra data: line 2 column 1 (char 145)
2025-10-06T05:58:58Z embeddings.ollama model=snowflake-arctic-embed2:568m in=87 out=1024
2025-10-06T05:58:58Z ingest.csv ok 49: Evidence for extensive horizontal gene transfer from the dra...
2025-10-06T05:58:58Z embeddings.ollama model=snowflake-arctic-embed2:568m in=114 out=1024
2025-10-06T05:59:10Z ingest.summarize.error Extra data: line 2 column 1 (char 145)
2025-10-06T05:59:13Z embeddings.ollama model=snowflake-arctic-embed2:568m in=114 out=1024
2025-10-06T05:59:13Z ingest.csv ok 50: Reply to Bemm et al. and Arakawa: Identifying foreign genes ...
2025-10-06T05:59:13Z ingest.csv done count=50
2025-10-06T05:59:13Z app.api_ingest_csv done inserted=50
INFO:     172.18.0.1:35330 - "POST /api/ingest_csv HTTP/1.1" 200 OK
```


## Implementation Notes
- Keep data open/public only.
- If OpenAI key exists, set it in `.env` to auto-enable.
- Universal Event submission deadline: Oct 5, 2025 23:59 local time.
- Summarization parser known issue (Ollama double-JSON handling). Functionality stable for embeddings; summaries partial.  
- All embeddings validated at 1024-D consistency across Qdrant and pgvector.

## Related Keywords
Space Biology, NASA OSDR, Knowledge Graph, RAG, Qdrant, pgvector, Embeddings, Summarization, Hybrid Search, Dashboard

## Known Issues

Frontend: The React dashboard builds and loads, but the search results are not displayed.
This is due to a networking or API variable issue (VITE_API_URL).
The backend, embeddings, and hybrid search all work correctly, and queries can be run directly via the API.
The UI portion was left unfinished due to time constraints.
Patch pending review to improve frontend API routing and response handling.

---
⭐ **If you find this useful for open science or AI RAG research, please star the repo.**  
© 2025 projectfong | MIT License
