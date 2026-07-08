"""Tests for RAGIndex._chunk_text.

These test invariants (properties that must always hold) rather than exact
chunk boundaries, so reasonable tweaks to the chunking algorithm don't
break the suite.
"""

from rag import RAGIndex

CHUNK = RAGIndex._chunk_text  # staticmethod: (text, chunk_size, overlap, min_chunk)


def test_short_text_single_chunk():
    text = "One short sentence."
    chunks = CHUNK(text, 500, 50, 250)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_chunks_are_nonempty_and_stripped():
    text = " ".join(f"Sentence number {i} is here." for i in range(60))
    chunks = CHUNK(text, 500, 50, 250)
    assert chunks, "expected at least one chunk"
    for c in chunks:
        assert c == c.strip()
        assert len(c) > 0


def test_all_content_is_covered():
    """Every sentence of the input should appear in at least one chunk."""
    sentences = [f"Unique sentence {i} ends here." for i in range(40)]
    text = " ".join(sentences)
    chunks = CHUNK(text, 500, 50, 250)
    joined = " ".join(chunks)
    for s in sentences:
        assert s in joined, f"lost content: {s!r}"


def test_chunk_size_roughly_respected():
    """Chunks should not wildly exceed chunk_size (small slack allowed for
    sentence-boundary snapping and the +10 hard-limit fudge)."""
    text = " ".join(f"Sentence number {i} is right here." for i in range(80))
    chunk_size = 300
    chunks = CHUNK(text, chunk_size, 50, 150)
    for c in chunks:
        assert len(c) <= chunk_size + 60, f"chunk too large: {len(c)} chars"


def test_single_giant_word_is_split_without_hanging():
    """A 'sentence' longer than chunk_size with no spaces must still
    terminate and produce chunks (regression guard for the word-boundary
    fallback path)."""
    text = "x" * 2000
    chunks = CHUNK(text, 500, 50, 250)
    assert chunks
    assert sum(len(c) for c in chunks) >= 2000 * 0.9  # allow boundary trims