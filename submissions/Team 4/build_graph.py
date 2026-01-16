import json
import networkx as nx
import pickle
import os

CLEAN_DATA_DIR = "./clean_data"   # directory with cleaned page JSONs
GRAPH_FILE = "graph.pkl"

G = nx.DiGraph()

print("📦 Building graph from cleaned data...")

for fname in os.listdir(CLEAN_DATA_DIR):
    if not fname.endswith(".json"):
        continue

    with open(os.path.join(CLEAN_DATA_DIR, fname), "r", encoding="utf-8") as f:
        page = json.load(f)

    src = page["title"]

    # Add node even if it has no edges
    G.add_node(src)

    for dst in page.get("edges", []):
        G.add_edge(src, dst)

print(f"✅ Graph built with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")

with open(GRAPH_FILE, "wb") as f:
    pickle.dump(G, f)

print(f"💾 Graph saved as {GRAPH_FILE}")
