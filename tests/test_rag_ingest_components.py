from app.rag.chunker import split_text
from app.rag.fetcher import infer_source_type
from app.rag.parser import clean_text
from app.rag.parser import parse_html


def test_infer_source_type() -> None:
    assert infer_source_type("https://example.com/doc") == "url"
    assert infer_source_type("/tmp/doc.txt") == "file"


def test_parse_html_extracts_title_and_text() -> None:
    title, text = parse_html("<html><head><title>Tech Sector</title></head><body><h1>AI rally</h1></body></html>")
    assert title == "Tech Sector"
    assert "AI rally" in text


def test_split_text_returns_multiple_chunks() -> None:
    text = "Paragraph one. " * 200
    chunks = split_text(text, chunk_size=200, overlap=40)
    assert len(chunks) > 1
    assert all(chunk for chunk in chunks)


def test_clean_text_normalizes_spacing() -> None:
    cleaned = clean_text("Alpha   \n\n\nBeta")
    assert cleaned == "Alpha \n\nBeta"
