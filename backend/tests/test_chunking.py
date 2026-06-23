from backend.app.services.knowledge_service import _chunk_text


def test_chunk_splits_oversized_paragraph():
    # A single 1500-word paragraph must be split so no chunk exceeds chunk_size.
    big = " ".join(["word"] * 1500)
    chunks = _chunk_text(big, chunk_size=512, overlap=50)
    assert len(chunks) >= 3
    assert all(len(c.split()) <= 512 for c in chunks)


def test_chunk_packs_small_paragraphs_into_one():
    text = "\n\n".join(["alpha beta gamma"] * 5)
    chunks = _chunk_text(text, chunk_size=512, overlap=10)
    assert len(chunks) == 1
    assert "alpha" in chunks[0]


def test_chunk_rolls_over_with_overlap():
    # Two paragraphs that together exceed chunk_size produce two chunks.
    p = " ".join(["x"] * 400)
    chunks = _chunk_text(f"{p}\n\n{p}", chunk_size=512, overlap=50)
    assert len(chunks) == 2


def test_chunk_empty_text():
    assert _chunk_text("") == []
