from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from .config import get_settings


def get_qdrant_client() -> QdrantClient:
    settings = get_settings()
    return QdrantClient(url=settings.qdrant_url, timeout=30)


def ensure_collection(vector_size: int) -> None:
    settings = get_settings()
    client = get_qdrant_client()
    names = {c.name for c in client.get_collections().collections}
    if settings.qdrant_collection in names:
        return
    client.create_collection(
        collection_name=settings.qdrant_collection,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )
