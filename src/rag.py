"""Retrieval-augmented generation: chunking, embedding, and querying bio docs."""

import re
import uuid
from dataclasses import dataclass

import chromadb
from chromadb import Collection
from openai import OpenAI

__all__ = ["RAGIndex"]


@dataclass
class RAGIndex:
    """Owns the embedding client and Chroma collection for one document set.

    Attributes:
        client: OpenAI client used to generate embeddings.
        collection: Chroma collection holding embedded document chunks.
    """

    client: OpenAI
    collection: Collection

    @classmethod
    def from_documents(
        cls,
        client: OpenAI,
        documents: list[dict],
        *,
        chunk_size: int = 500,
        overlap: int = 50,
        min_chunk: int = 250,
        db_path: str = "./chroma_db_twin_4",
        collection_name: str = "digital_twin",
    ) -> "RAGIndex":
        """Chunk, embed, and load documents into a fresh Chroma collection.

        Args:
            client: OpenAI client used for embeddings.
            documents: List of {"text": str, "source": str} dicts.
            chunk_size: Target characters per chunk.
            overlap: Character overlap between adjacent chunks.
            min_chunk: Minimum characters before a chunk boundary is accepted.
            db_path: Local path for the Chroma persistent store.
            collection_name: Name of the Chroma collection to use.

        Returns:
            A ready-to-query RAGIndex.
        """
        chunks, ids, metadatas = [], [], []
        for doc in documents:
            doc_chunks = cls._chunk_text(doc["text"], chunk_size, overlap, min_chunk)
            doc_ids = [str(uuid.uuid4()) for _ in doc_chunks]
            doc_meta = [
                {"source": doc["source"], "chunk_index": i}
                for i in range(len(doc_chunks))
            ]
            chunks.extend(doc_chunks)
            ids.extend(doc_ids)
            metadatas.extend(doc_meta)

        response = client.embeddings.create(model="text-embedding-3-small", input=chunks)
        embeddings = [item.embedding for item in response.data]

        chroma_client = chromadb.PersistentClient(path=db_path)
        collection = chroma_client.get_or_create_collection(name=collection_name)

        existing_ids = collection.get()["ids"]
        if existing_ids:
            collection.delete(ids=existing_ids)

        collection.add(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)
        print(f"RAGIndex: loaded {len(chunks)} chunks from {len(documents)} documents")

        return cls(client=client, collection=collection)

    @staticmethod
    def _chunk_text(text: str, chunk_size: int, overlap: int, min_chunk: int) -> list[str]:
        """Split text into overlapping, sentence-aligned chunks."""
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

    def retrieve_context(self, query: str, n_results: int = 3) -> str:
        """Embed a query, retrieve nearest chunks (with 1-chunk neighbor padding).

        Args:
            query: The user's message to retrieve context for.
            n_results: Number of nearest chunks to retrieve.

        Returns:
            A formatted context string ready to append to the system prompt.
        """
        response = self.client.embeddings.create(model="text-embedding-3-small", input=[query])
        query_embeddings = [item.embedding for item in response.data]

        results = self.collection.query(
            query_embeddings=query_embeddings,
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )
        all_rows = self.collection.get(include=["documents", "metadatas"])

        context_blocks = []
        for i in range(min(n_results, len(results["metadatas"][0]))):
            meta_i = results["metadatas"][0][i]
            src = meta_i["source"]
            ix = meta_i["chunk_index"]
            wanted = {ix - 1, ix, ix + 1}
            pairs = [
                (meta["chunk_index"], doc)
                for meta, doc in zip(all_rows["metadatas"], all_rows["documents"])
                if meta["source"] == src and meta["chunk_index"] in wanted
            ]
            pairs.sort(key=lambda x: x[0])
            context_blocks.append("\n\n".join(d for _, d in pairs))


        return "\n\n---\n\n".join(context_blocks)

    def __repr__(self) -> str:
        return f"RAGIndex(chunks={self.collection.count()})"