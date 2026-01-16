import json
import faiss
import pickle
import re
from sentence_transformers import SentenceTransformer
from google import genai
from dotenv import load_dotenv
import os

# =========================================================
# CONFIG
# =========================================================
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

FAISS_INDEX_FILE = "metakgp.faiss"
CHUNK_METADATA_FILE = "chunk_metadata.json"
GRAPH_FILE = "graph.pkl"

TOP_K = 5
MAX_CONTEXT_CHUNKS = 8
MAX_GOT_HOPS = 1
MAX_GOT_PAGES = 10

GEMINI_MODEL = "gemini-2.5-flash"

# =========================================================
# LOAD ENV + RESOURCES (ONCE)
# =========================================================
load_dotenv()

print("📦 Loading resources...")

# Embedding model
embed_model = SentenceTransformer(EMBEDDING_MODEL)

# FAISS index
faiss_index = faiss.read_index(FAISS_INDEX_FILE)

# Chunk metadata
with open(CHUNK_METADATA_FILE, "r", encoding="utf-8") as f:
    ALL_CHUNKS = json.load(f)

# Graph
with open(GRAPH_FILE, "rb") as f:
    GRAPH = pickle.load(f)

# Gemini client
gemini_client = genai.Client()

print("✅ All resources loaded")

# =========================================================
# STEP 1: FAISS RETRIEVAL
# =========================================================
def retrieve_chunks(query, top_k=TOP_K):
    query_embedding = embed_model.encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    scores, indices = faiss_index.search(query_embedding, top_k)
    return [ALL_CHUNKS[i] for i in indices[0]]

# =========================================================
# STEP 2: GENERAL GRAPH OF THOUGHTS (GoT)
# =========================================================
def apply_got(retrieved_chunks, max_hops=MAX_GOT_HOPS, max_pages=MAX_GOT_PAGES):
    """
    General, query-agnostic GoT expansion.
    """
    start_pages = {c["page"] for c in retrieved_chunks}

    expanded_pages = set(start_pages)
    frontier = set(start_pages)

    for _ in range(max_hops):
        next_frontier = set()

        for page in frontier:
            if page not in GRAPH:
                continue

            for neighbor in GRAPH.neighbors(page):
                if neighbor not in expanded_pages:
                    next_frontier.add(neighbor)

        expanded_pages.update(next_frontier)
        frontier = next_frontier

        if len(expanded_pages) >= max_pages:
            break

    return expanded_pages

# =========================================================
# STEP 3: CONTEXT BUILDER
# =========================================================
def collect_context_chunks(retrieved_chunks, expanded_pages):
    """
    Selects the final chunks that the LLM is allowed to see.
    """
    final_chunks = []
    seen = set()

    # Always include FAISS chunks first (highest precision)
    for c in retrieved_chunks:
        if c["chunk_id"] not in seen:
            final_chunks.append(c)
            seen.add(c["chunk_id"])

    # Add GoT-related chunks
    for c in ALL_CHUNKS:
        if c["page"] in expanded_pages:
            if c["chunk_id"] not in seen:
                final_chunks.append(c)
                seen.add(c["chunk_id"])

        if len(final_chunks) >= MAX_CONTEXT_CHUNKS:
            break

    return final_chunks


# Code for parsing gemini output to json
def safe_parse_json(text):
    """
    Extracts first valid JSON object from Gemini output.
    """
    try:
        # Direct parse
        return json.loads(text)
    except Exception:
        pass

    # Remove markdown fences
    text = text.strip()
    text = re.sub(r"^```json", "", text)
    text = re.sub(r"^```", "", text)
    text = re.sub(r"```$", "", text)
    text = text.strip()

    # Extract JSON substring
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except Exception:
            pass

    return None


# =========================================================
# STEP 4: LLM GENERATION (STRICT RAG) — GEMINI
# =========================================================
def generate_answer_llm(query, context_chunks):
    """
    Gemini-based STRICT RAG generation.
    Returns a dict: { "answer": ..., "sources": [...] }
    """

    # Build structured context
    context_payload = []
    for c in context_chunks:
        context_payload.append({
            "page": c["page"],
            "section": c["section"],
            "text": c["text"],
            "url": c["url"]
        })

    prompt = """
You are a factual assistant.

STRICT RULES:
- Use ONLY the provided context.
- Do NOT use any external or prior knowledge.
- Do NOT guess or infer beyond the text.
- If the answer is not explicitly stated, reply exactly:
  "I don't know."
- Every factual claim MUST be supported by a source URL.

Return ONLY valid JSON in this format:
{
  "answer": "<answer text or 'I don't know.'>",
  "sources": ["<url1>", "<url2>"]
}
"""

    payload = {
        "prompt": prompt,
        "question": query,
        "context": context_payload
    }

    response = gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=json.dumps(payload)
    )

    if not response.text:
        return {"answer": "I don't know.", "sources": []}

    parsed = safe_parse_json(response.text)
    if not parsed:
        return {"answer": "I don't know.", "sources": []}
    
    return parsed 

# =========================================================
# STEP 5: MoE VERIFICATION
# =========================================================
def verify_answer(answer_obj, context_chunks):
    """
    Source-grounded MoE (correct for RAG systems)
    """

    answer_text = answer_obj.get("answer", "").strip()
    sources = answer_obj.get("sources", [])

    # 1. Explicit "I don't know" is always allowed
    if answer_text.lower() == "i don't know.":
        return True

    # 2. Must cite at least one source
    if not sources:
        return False

    # 3. Every cited source must come from retrieved context
    allowed_urls = {c["url"] for c in context_chunks}
    for src in sources:
        if src not in allowed_urls:
            return False

    # 4. Answer must not be empty / trivial
    if len(answer_text) < 10:
        return False

    return True


# =========================================================
# FULL PIPELINE
# =========================================================
def answer_query(query):
    # 1. Retrieval
    retrieved_chunks = retrieve_chunks(query)

    # 2. Graph of Thoughts
    expanded_pages = apply_got(retrieved_chunks)

    # 3. Context building
    context_chunks = collect_context_chunks(retrieved_chunks, expanded_pages)

    # 4. LLM generation
    answer_obj = generate_answer_llm(query, context_chunks)

    # 5. Verification
    if not verify_answer(answer_obj, context_chunks):
        return {
            "answer": "I don't know.",
            "sources": []
        }

    return answer_obj

# =========================================================
# CLI DEMO
# =========================================================
if __name__ == "__main__":
    print("\n🧠 MetaKGP GraphMind (RAG + GoT)")
    print("Type 'exit' to quit.")

    while True:
        query = input("\n❓ Question: ").strip()
        if query.lower() == "exit":
            break

        result = answer_query(query)

        print("\n💡 Answer:")
        print(result["answer"])

        if result["sources"]:
            print("\n🔗 Sources:")
            for s in result["sources"]:
                print("-", s)


def answer_query_api(query: str):
    return answer_query(query)
