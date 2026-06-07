"""
embed.py — Milestone 4: Embedding + Vector Store + Retrieval

Stage 3 (Embedding & Store) and Stage 4 (Retrieval) of the architecture:
    - Loads the chunks produced by chunks.py (chunks.json).
    - Embeds each chunk into a 384-dimensional dense vector with
      all-MiniLM-L6-v2 (sentence-transformers).
    - Upserts vectors + text + metadata into a persistent local ChromaDB
      collection (cosine space).
    - Provides retrieve() to embed a query and return the top-k chunks.

Usage:
    python embed.py                      # (re)build the index, then run a demo query
    python embed.py --query "your question here"   # build if needed, then retrieve
    python embed.py --top-k 5 --query "..."
"""

import argparse
import json
import os

import chromadb
from sentence_transformers import SentenceTransformer

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

CHUNKS_FILE = "chunks.json"
CHROMA_DIR = "chroma_db"
COLLECTION_NAME = "rutgers_unofficial_guide"
MODEL_NAME = "all-MiniLM-L6-v2"  # 384-dimensional vectors
DEFAULT_TOP_K = 3

# A sample question from the Evaluation Plan, used for the demo run.
DEMO_QUERY = "What maintenance issues did students face at The Standard apartments?"


# --------------------------------------------------------------------------- #
# Model + client (loaded once, reused)
# --------------------------------------------------------------------------- #

_model = None


def get_model():
    """Load (and cache) the sentence-transformers embedding model."""
    global _model
    if _model is None:
        print(f"Loading embedding model '{MODEL_NAME}'...")
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def get_collection():
    """Open (or create) the persistent ChromaDB collection."""
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def embed_texts(texts):
    """Embed a list of texts into normalized 384-dim vectors (as lists)."""
    model = get_model()
    vectors = model.encode(
        texts,
        normalize_embeddings=True,   # unit vectors pair well with cosine space
        show_progress_bar=False,
    )
    return vectors.tolist()


# --------------------------------------------------------------------------- #
# Index building
# --------------------------------------------------------------------------- #

def reddit_id_from_url(url):
    """Pull the Reddit post id out of a permalink for use in chunk ids."""
    parts = [p for p in url.split("/") if p]
    if "comments" in parts:
        idx = parts.index("comments")
        if idx + 1 < len(parts):
            return parts[idx + 1]
    return "thread"


def load_chunks():
    """Load chunk records from chunks.json."""
    if not os.path.exists(CHUNKS_FILE):
        raise FileNotFoundError(
            f"{CHUNKS_FILE} not found. Run chunks.py first."
        )
    with open(CHUNKS_FILE, "r", encoding="utf-8") as handle:
        return json.load(handle)


def build_index():
    """Embed every chunk and upsert it into the ChromaDB collection.

    Uses deterministic ids (<post_id>_<chunk_index>) so re-running updates
    rows in place rather than creating duplicates.
    """
    chunks = load_chunks()
    collection = get_collection()

    ids, documents, metadatas = [], [], []
    for chunk in chunks:
        post_id = reddit_id_from_url(chunk.get("source_url", ""))
        ids.append(f"{post_id}_{chunk['chunk_index']}")
        documents.append(chunk["text"])
        metadatas.append({
            "post_title": chunk.get("post_title", ""),
            "source_url": chunk.get("source_url", ""),
            "chunk_index": chunk["chunk_index"],
        })

    print(f"Embedding {len(documents)} chunks...")
    embeddings = embed_texts(documents)
    print(f"Vector dimension: {len(embeddings[0])}")

    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )

    count = collection.count()
    print(f"Collection '{COLLECTION_NAME}' now holds {count} vectors "
          f"(expected {len(chunks)}).")
    return collection


# --------------------------------------------------------------------------- #
# Retrieval (Stage 4)
# --------------------------------------------------------------------------- #

def retrieve(query, top_k=DEFAULT_TOP_K, collection=None):
    """Embed the query and return the top-k most similar chunks.

    Returns a list of dicts: {text, post_title, source_url, chunk_index,
    distance}, ordered most-relevant first.
    """
    if collection is None:
        collection = get_collection()

    query_vector = embed_texts([query])[0]
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    hits = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        hits.append({
            "text": doc,
            "post_title": meta.get("post_title", ""),
            "source_url": meta.get("source_url", ""),
            "chunk_index": meta.get("chunk_index"),
            "distance": dist,
        })
    return hits


def print_hits(query, hits):
    """Pretty-print retrieval results for manual inspection."""
    print(f"\nQuery: {query}")
    print(f"Top {len(hits)} chunks:\n")
    for rank, hit in enumerate(hits, start=1):
        preview = hit["text"].replace("\n", " ")
        if len(preview) > 220:
            preview = preview[:220] + "..."
        print(f"[{rank}] distance={hit['distance']:.4f} | "
              f"{hit['post_title'][:50]} (chunk {hit['chunk_index']})")
        print(f"    {preview}")
        print(f"    source: {hit['source_url']}\n")


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main():
    parser = argparse.ArgumentParser(description="Build the vector index and/or query it.")
    parser.add_argument("--query", help="Run a retrieval for this question.")
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K,
                        help="Number of chunks to retrieve (default 3).")
    parser.add_argument("--no-build", action="store_true",
                        help="Skip rebuilding the index; query the existing one.")
    args = parser.parse_args()

    collection = get_collection() if args.no_build else build_index()

    query = args.query or DEMO_QUERY
    hits = retrieve(query, top_k=args.top_k, collection=collection)
    print_hits(query, hits)


if __name__ == "__main__":
    main()
