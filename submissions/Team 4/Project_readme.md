# GraphMind – Verified Conversational AI for MetaKGP

---

## 🏷️ Team Information

**Team Name:** Team 4

### 👥 Team Members
- **Member 1:** [Dhruv]
- **Member 2:** [Piyush] 
- **Member 3:** [Jatin]  
- **Member 4:** [Harshita]

---

## 🔗 Project Links

- **Demo Video:** [YouTube / Loom link – 3–5 minutes]  
---

## 🧠 Project Overview

GraphMind is a **verified conversational AI system** built for the  
**DevSoc 2026 Hackathon – Advanced LLM Reasoning & Verification Challenge**.

The goal of the challenge is to solve the problem of **hallucinations in LLMs**
when answering **institution-specific queries** related to IIT Kharagpur.

GraphMind answers questions **strictly using data scraped from MetaKGP /
MetaWiki** and **never uses external knowledge**.

If the required information is not explicitly present in MetaKGP, the system
responds with:

> **“I don’t know.”**

This behavior is enforced by design using:
- Retrieval-Augmented Generation (RAG)
- Graph of Thoughts (GoT)
- Source-grounded Mixture of Experts (MoE)

---

## 🤖 Technical Implementation

---

### 1️⃣ Data Pipeline (Scraping)

#### 🔧 Tools Used
- `mwclient` – MediaWiki API access
- `mwparserfromhell` – WikiText parsing and cleaning
- `BeautifulSoup` – fallback HTML parsing
- Python standard libraries

#### 📌 Scraping Strategy
- Pages are fetched **directly from `wiki.metakgp.org`** using the MediaWiki API
- Raw **WikiText** is extracted for each page
- Wiki links are extracted to form graph edges
- No pre-downloaded dumps or external datasets are used (strictly enforced)

#### 🧹 Cleaning Strategy
- Removed non-informational sections:
  - Categories
  - Timetables
  - Tools / Appearance / Navigation
- Cleaned Wiki markup using `mwparserfromhell`
- Normalized whitespace and duplicate headings
- Retained only semantically meaningful content

# MetaKGP Project

**Overview**
- **Purpose:** A small RAG (retrieval-augmented generation) + Graph-of-Thoughts system built on MetaKGP wiki data. The pipeline scrapes wiki pages, cleans and chunks them, builds a graph of page links, creates dense embeddings (FAISS), and serves a strict RAG API via FastAPI.

**Quick Start (typical pipeline order)**
- **1. Scrape pages:** run the scraper to fetch raw pages into data/.
  - File: [scraper.py](scraper.py)
- **2. Clean & chunk pages:** run the cleaner and chunker to produce per-page cleaned JSONs and a single chunks list in `chunked_data/`.
  - File: [cleaner_chunker.py](cleaner_chunker.py)
  - Optional small cleaner that strips newlines: [cleaner.py](cleaner.py)
- **3. Build page graph:** build `graph.pkl` from cleaned pages (uses `edges` saved during scraping).
  - File: [build_graph.py](build_graph.py)
- **4. Create embeddings & FAISS index:** create vector embeddings from chunks and save `metakgp.faiss` and `chunk_metadata.json`.
  - File: [embedder.py](embedder.py)
- **5. Run the RAG engine locally:** the main retrieval+GoT+LLM code lives here — it loads FAISS, chunk metadata and graph, and provides `answer_query`.
  - File: [rag_engine.py](rag_engine.py)
- **6. Optional GOT helper:** a standalone Graph-of-Thoughts expansion helper.
  - File: [got.py](got.py)
- **7. API server:** FastAPI wrapper exposing `/query` which calls the RAG engine.
  - File: [app.py](app.py)

**File-by-file summary (in pipeline order)**
- **[scraper.py](scraper.py):** Connects to the MediaWiki instance (`wiki.metakgp.org`) using `mwclient`, iterates pages, parses wikitext with `mwparserfromhell` into section-level chunks, collects outgoing links, and writes one JSON file per page into the configured output directory (default `data/`). Important keys written: `title`, `url`, `sections` (list of `{heading, text}`), `edges` (linked pages).

- **[cleaner_chunker.py](cleaner_chunker.py):** Two responsibilities: (1) `run_cleaning()` — removes unwanted sections, normalizes text, and produces cleaned per-page JSON files in `clean_data/`; (2) `chunk_data()` — converts each cleaned page's sections into chunk objects of the form `{chunk_id, page, section, text, url}` and writes them to `chunked_data/` (used by embedding). The script includes heuristics to drop ‘References’, ‘External links’, tiny sections, and to normalize whitespace.

- **[cleaner.py](cleaner.py):** A small utility added to remove newline/carriage-return characters from JSON string values across files. Useful as a pre-step if your text contains stray newlines.

- **[build_graph.py](build_graph.py):** Reads cleaned page JSONs from `clean_data/`, constructs a directed NetworkX graph using the `edges` field (source page -> linked page), and saves the graph as `graph.pkl`. This graph is used by the GOT expansion step.

- **[embedder.py](embedder.py):** Loads the chunk list from `chunked_data/chunks.json`, composes a context-aware string for each chunk (prefixing `Page:` and `Section:`), encodes them with a SentenceTransformers model (`all-MiniLM-L6-v2`), builds a FAISS index (cosine via normalized vectors), and writes two artifacts: `metakgp.faiss` (the index) and `chunk_metadata.json` (the list of chunk objects in the same order as the vectors).

- **[got.py](got.py):** A compact utility that loads `graph.pkl` and performs bounded Graph-of-Thoughts expansion: starting from pages present in retrieved chunks, it walks neighbors up to `max_hops` and returns a set of expanded pages (used by the RAG engine to broaden context).

- **[rag_engine.py](rag_engine.py):** The core runtime pipeline:
  - Loads resources once: embedding model, FAISS index (`metakgp.faiss`), chunk metadata (`chunk_metadata.json`), and `graph.pkl`.
  - Retrieval: vector-search via FAISS to get top-k chunks.
  - GOT expansion: expand pages using the graph to gather related chunks.
  - Context builder: merge FAISS chunks and GOT chunks into a bounded context list.
  - LLM generation: calls Gemini (via `google.genai`) with a strict prompt that forces answers to use only provided context and to return JSON `{answer, sources}`.
  - Verification (MoE): enforces that every cited source appears in the context and that the answer is non-trivial; otherwise returns `I don't know.`
  - Exposes `answer_query(query)` and a thin `answer_query_api()` wrapper used by the API server.

- **[app.py](app.py):** FastAPI server that defines the `/query` POST endpoint. It accepts a JSON body with `question` and returns `{answer, sources}` by calling `rag_engine.answer_query_api`.

**Artifacts & folders**
- `chunked_data/chunks.json` — list of chunk objects used for embedding.
- `chunk_metadata.json` — metadata saved by `embedder.py` (mirrors `chunks.json` order).
- `metakgp.faiss` — FAISS index of vectors created by `embedder.py`.
- `graph.pkl` — pickled NetworkX graph created by `build_graph.py`.
- `clean_data/` — cleaned per-page JSONs produced by `cleaner_chunker.py`.

**Common commands**
Run the full pipeline (example):
```bash
# install dependencies
pip install -r requirements.txt

# 1. Scrape pages into data/
python scraper.py

# 2. Clean & chunk (produces clean_data/ and chunked_data/)
python cleaner_chunker.py

# 3. Build the page graph
python build_graph.py

# 4. Create embeddings + faiss index
python embedder.py

# 5. Run API server (FastAPI, default port 8000)
uvicorn app:app --host 0.0.0.0 --port 8000 --reload

# Running Frontend 
cd devsoc_frontend
npm i 
npm run dev
```



**Notes & tips**
- The FAISS index and `chunk_metadata.json` must remain in sync — do not reorder `chunk_metadata.json` after building the index.
- `rag_engine.py` expects `metakgp.faiss`, `chunk_metadata.json`, and `graph.pkl` to exist in the repository root.
- If you use a different embedding model or LLM, update the constants in `embedder.py` and `rag_engine.py` respectively.
- Use `--dry-run` in `cleaner.py` (if invoked) to preview changes before overwriting files.

If you want, I can also:
- Print a sample chunk from `chunked_data/chunks.json`.
- Show a short example of querying the running API and printing the raw RAG context.
