# src/rag.py
import re
import uuid
import chromadb
from config import client

# -----------------------
# RAG: Chunk
# -----------------------
def chunk_text(text, chunk_size=500, overlap=50, min_chunk=250):
    sents = list(re.finditer(r'\S.*?(?:[.!?](?=\s|$)|$)', text, re.S))
    chunks, i = [], 0
    while i < len(sents):
        start = sents[i].start()
        target = start + chunk_size
        hard = min(start + chunk_size + 10, len(text))
        ends = [m.end() for m in sents[i:] if m.end() <= hard]
        ends = [e for e in ends if e - start >= min_chunk] or ends
        if ends:
            end = min(ends, key=lambda e: abs(e - target))
        else:
            end = hard
            while end < len(text) and not text[end].isspace():
                end += 1
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        overlap_at = max(start + 1, end - overlap)
        prev_starts = [k for k, m in enumerate(sents) if start < m.start() <= overlap_at]
        i = prev_starts[-1] if prev_starts else i + 1
    return chunks

def build_index(documents):
    """Chunk, embed, and load into Chroma. Call once at app startup."""
    chunks, ids, metadatas = [], [], []
    for doc in documents:
        chunks_ = chunk_text(doc["text"], chunk_size=500, overlap=50, min_chunk=250)
        ids_ = [str(uuid.uuid4()) for _ in chunks_]
        metadatas_ = [{"source": doc["source"], "chunk_index": i} for i in range(len(chunks_))]
        chunks.extend(chunks_)
        ids.extend(ids_)
        metadatas.extend(metadatas_)

    response = client.embeddings.create(model="text-embedding-3-small", input=chunks)
    embeddings = [item.embedding for item in response.data]

    chroma_client = chromadb.PersistentClient(path="./chroma_db_twin_4")
    collection = chroma_client.get_or_create_collection(name="digital_twin")

    existing_ids = collection.get()["ids"]
    if existing_ids:
        collection.delete(ids=existing_ids)

    collection.add(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)
    print("num_chunks:", len(chunks))
    return collection