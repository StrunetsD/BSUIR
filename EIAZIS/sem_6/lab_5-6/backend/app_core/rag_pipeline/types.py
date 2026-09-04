from dataclasses import dataclass


@dataclass(frozen=True)
class SourceDocument:
    title: str
    text: str
    author: str | None = None
    source: str | None = None


@dataclass(frozen=True)
class TextChunk:
    chunk_index: int
    text: str


@dataclass(frozen=True)
class EmbeddedChunk:
    chunk_index: int
    text: str
    vector: list[float]
