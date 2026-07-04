from typing import List
import re
import logfire


def _recursive_split(text: str, chunk_size: int) -> List[str]:
    """
    Recursively split text so that every returned chunk is <= chunk_size.
    Tries progressively smaller semantic boundaries.
    """
    if len(text) <= chunk_size:
        return [text.strip()]

    # Try paragraph split
    if "\n\n" in text:
        parts = text.split("\n\n")
        separator = "\n\n"

    # Then line split
    elif "\n" in text:
        parts = text.split("\n")
        separator = "\n"

    # Then sentence split
    elif re.search(r'(?<=[.!?])\s+', text):
        parts = re.split(r'(?<=[.!?])\s+', text)
        separator = " "

    # Then word split
    elif " " in text:
        parts = text.split(" ")
        separator = " "

    # Last resort: character split
    else:
        return [
            text[i:i + chunk_size]
            for i in range(0, len(text), chunk_size)
        ]

    chunks = []
    current = ""

    for part in parts:
        candidate = part if not current else current + separator + part

        if len(candidate) <= chunk_size:
            current = candidate
        else:
            if current:
                chunks.extend(_recursive_split(current, chunk_size))
            current = part

    if current:
        chunks.extend(_recursive_split(current, chunk_size))

    return chunks


def chunk_text(text: str, chunk_size: int = 1500) -> List[str]:
    """
    Semantic chunker with recursive fallback.

    Guarantees:
    - No chunk exceeds chunk_size.
    - Prefers paragraphs.
    - Falls back to lines, sentences, words, then characters.
    """
    with logfire.span("Text Chunking", text_length=len(text)):
        if not text.strip():
            return []

        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")

        chunks = _recursive_split(text, chunk_size)

        chunks = [chunk.strip() for chunk in chunks if chunk.strip()]

        logfire.info(
            f"Generated {len(chunks)} chunks",
            max_chunk_size=max((len(c) for c in chunks), default=0),
        )

        return chunks