#!/usr/bin/env python3
import os
import sys
import sqlite3
import numpy as np
import hashlib

DB_PATH = "/root/.openclaw/workspace/memory/vector_index.db"

def get_embedding(text):
    np.random.seed(int(hashlib.md5(text.encode()).hexdigest()[:8], 16))
    return np.random.rand(384).astype(np.float32)

def cosine_similarity(v1, v2):
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

def search(query, top_k=3):
    if not os.path.exists(DB_PATH):
        print("Index not found. Run auto_indexer.py first.")
        return
        
    query_emb = get_embedding(query)
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT source_file, content, embedding FROM memory_chunks")
    
    results = []
    for row in c.fetchall():
        source, content, emb_bytes = row
        emb = np.frombuffer(emb_bytes, dtype=np.float32)
        score = cosine_similarity(query_emb, emb)
        results.append((score, source, content))
        
    results.sort(reverse=True, key=lambda x: x[0])
    
    for i, (score, source, content) in enumerate(results[:top_k]):
        print(f"[{source}] (Score: {score:.2f})")
        print(f"{content}\n")
        
    conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: ./search_memory.py 'your query'")
        sys.exit(1)
    search(sys.argv[1])