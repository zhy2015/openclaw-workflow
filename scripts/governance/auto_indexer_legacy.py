#!/usr/bin/env python3
import os
import json
import sqlite3
import hashlib
from datetime import datetime
import numpy as np
import urllib.request
import urllib.parse

# Configurations
MEMORY_DIR = "/root/.openclaw/workspace/memory/daily"
ARCHIVE_DIR = "/root/.openclaw/workspace/memory/archive"
DB_PATH = "/root/.openclaw/workspace/memory/vector_index.db"
OLLAMA_EMBED_URL = "http://localhost:11434/api/embeddings"  # Fallback
API_KEY = "dummy" # Assuming local/proxy handling for external if needed, or fallback to simple TF-IDF if no embedder.

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS memory_chunks (
            id TEXT PRIMARY KEY,
            source_file TEXT,
            content TEXT,
            timestamp DATETIME,
            embedding BLOB
        )
    ''')
    conn.commit()
    return conn

def get_embedding(text):
    # For now, using a placeholder fast hashing/TF-IDF simulation 
    # since we don't know the exact local embedder API available to the host.
    # In a real setup, this calls a local sentence-transformer or API.
    # We will use a deterministic pseudo-embedding based on hash for scaffolding.
    np.random.seed(int(hashlib.md5(text.encode()).hexdigest()[:8], 16))
    return np.random.rand(384).astype(np.float32)

def process_file(filepath, conn):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split by list items or double newlines (simple chunking)
    chunks = [c.strip() for c in content.split('\n-') if c.strip()]
    
    c = conn.cursor()
    added = 0
    for chunk in chunks:
        if not chunk: continue
        chunk = "- " + chunk if not chunk.startswith("-") else chunk
        
        chunk_id = hashlib.md5(chunk.encode()).hexdigest()
        
        # Check if exists
        c.execute("SELECT id FROM memory_chunks WHERE id=?", (chunk_id,))
        if c.fetchone():
            continue
            
        emb = get_embedding(chunk)
        c.execute(
            "INSERT INTO memory_chunks (id, source_file, content, timestamp, embedding) VALUES (?, ?, ?, ?, ?)",
            (chunk_id, os.path.basename(filepath), chunk, datetime.now(), emb.tobytes())
        )
        added += 1
    
    conn.commit()
    return added

def index_memories():
    conn = init_db()
    total_added = 0
    
    dirs_to_check = [MEMORY_DIR, ARCHIVE_DIR]
    
    for d in dirs_to_check:
        if not os.path.exists(d): continue
        for filename in os.listdir(d):
            if filename.endswith(".md"):
                added = process_file(os.path.join(d, filename), conn)
                total_added += added
                
    conn.close()
    print(f"Index updated. Added {total_added} new memory chunks.")

if __name__ == "__main__":
    index_memories()