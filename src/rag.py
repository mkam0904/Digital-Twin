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
        else:  # single sentence > chunk_size: split at word boundary
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

# -----------------------
# RAG: Chunk
# -----------------------

chunks = []
ids = []
metadatas = []

for i, doc in enumerate(documents, 1): 
    chunks_ = chunk_text(doc['text'], chunk_size=500, overlap=50, min_chunk=250)
    ids_ = [str(uuid.uuid4()) for _ in range(len(chunks_))]
    metadatas_ = [{"source":doc['source'], "chunk_index":i} for i in range(len(chunks_))]

    chunks.extend(chunks_)
    ids.extend(ids_)
    metadatas.extend(metadatas_)

if 0: 
    print('total chunks: ', len(chunks)) 
    for i, c in enumerate(chunks):
        print(f"Chunk {i} ({len(c)} chars) ──")
        print(f"ids[{i}]: {ids[i]}")
        print(f"metadatas{i}: {metadatas[i]}")
        print(c)
        print()

response = client.embeddings.create( 
    model = "text-embedding-3-small",
    input = chunks
)
embeddings = [item.embedding for item in response.data]

# -----------------------
# RAG: ChromaDB
# -----------------------
import chromadb

debug_chromadb = 0
chroma_client = chromadb.PersistentClient(path = "./chroma_db_twin_4")

# Get or create + Empty the collection before adding new data (for testing purpose) 
collection = chroma_client.get_or_create_collection(name="digital_twin")
if debug_chromadb: 
    print('ids:',collection.get()["ids"])

# Empty the collection before adding new data (for testing purpose) 
if collection.get()["ids"]:
    collection.delete(ids=collection.get()["ids"])

# Prepare data for storage 
print("num_chunks: ",len(chunks))

# Adding data to chromadb
collection.add(
    ids = ids,
    embeddings = embeddings,
    documents = chunks,
    metadatas = metadatas
)

# Chroma hides embeddings unless you ask for them 
for k in collection.get().keys():  
    c = collection.get(include=["embeddings", "documents", "metadatas"])[k]
    if isinstance(c,list):
        print('-' * 25)
        print(f"{k}: ix0: {c[0]} ...")
        print(f"\tix[n-1]: {c[len(c)-1]}")
    else: 
        print(f"{k}: {type(c)}")
print('-' * 25)


