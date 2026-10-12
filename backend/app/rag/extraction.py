from __future__ import annotations

import re
from pathlib import Path
from docx import Document
from pypdf import PdfReader


def extract_text(path: Path) -> tuple[str, list[dict]]:
    ext = path.suffix.lower()
    if ext == ".pdf":
        pages = []
        texts = []
        reader = PdfReader(str(path))
        for i, page in enumerate(reader.pages, 1):
            text = page.extract_text() or ""
            if text.strip():
                texts.append(text)
                pages.append({"page": i, "text": text})
        return "\n\n".join(texts), pages
    if ext == ".docx":
        doc = Document(str(path))
        blocks = []
        texts = []
        for i, p in enumerate(doc.paragraphs, 1):
            if p.text.strip():
                texts.append(p.text)
                blocks.append({"paragraph": i, "text": p.text})
        return "\n".join(texts), blocks
    raise ValueError("Formato no admitido")


def chunk_text(text: str, window_tokens: int = 512, overlap_tokens: int = 50) -> list[str]:
    tokens = re.findall(r"\S+", text)
    if not tokens:
        return []
    step = max(1, window_tokens - overlap_tokens)
    chunks: list[str] = []
    for start in range(0, len(tokens), step):
        piece = tokens[start : start + window_tokens]
        if not piece:
            break
        joined = " ".join(piece).strip()
        if len(joined) >= 20:
            chunks.append(joined)
        if start + window_tokens >= len(tokens):
            break
    return chunks
