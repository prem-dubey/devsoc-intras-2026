import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# -----------------------------
# CONFIG
# -----------------------------
CHUNKS_FILE = "./chunked_data/chunks.json"          # 🔥 rename your 478.json to chunks.json
FAISS_INDEX_FILE = "metakgp.faiss"
METADATA_FILE = "chunk_metadata.json"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
MIN_TEXT_LENGTH = 30                 # safety filter


# -----------------------------
# LOAD CHUNKS
# -----------------------------
print("📄 Loading chunks...")
with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
    raw_chunks = json.load(f)

chunks = []
texts = []

for c in raw_chunks:
    text = c.get("text", "").strip()
    if len(text) < MIN_TEXT_LENGTH:
        continue

    # Context-aware embedding text
    embed_text = (
        f"Page: {c['page']}\n"
        f"Section: {c['section']}\n\n"
        f"{text}"
    )

    chunks.append(c)
    texts.append(embed_text)

print(f"✅ Loaded {len(chunks)} valid chunks")


# -----------------------------
# LOAD EMBEDDING MODEL
# -----------------------------
print("🧠 Loading embedding model...")
model = SentenceTransformer(EMBEDDING_MODEL_NAME)


# -----------------------------
# CREATE EMBEDDINGS
# -----------------------------
print("🔢 Creating embeddings...")
embeddings = model.encode(
    texts,
    batch_size=32,
    show_progress_bar=True,
    convert_to_numpy=True,
    normalize_embeddings=True   # REQUIRED for cosine similarity
)

print(f"✅ Embeddings shape: {embeddings.shape}")


# -----------------------------
# BUILD FAISS INDEX (COSINE SIM)
# -----------------------------
print("📦 Building FAISS index...")

dimension = embeddings.shape[1]
index = faiss.IndexFlatIP(dimension)
index.add(embeddings)

assert index.ntotal == len(chunks), "❌ FAISS index and chunk count mismatch"

print(f"✅ FAISS index contains {index.ntotal} vectors")


# -----------------------------
# SAVE INDEX + METADATA
# -----------------------------
print("💾 Saving FAISS index...")
faiss.write_index(index, FAISS_INDEX_FILE)

print("💾 Saving chunk metadata...")
with open(METADATA_FILE, "w", encoding="utf-8") as f:
    json.dump(chunks, f, indent=2, ensure_ascii=False)

print("🎉 Embedding + indexing completed successfully!")
print(f"➡️ FAISS index: {FAISS_INDEX_FILE}")
print(f"➡️ Metadata  : {METADATA_FILE}")
