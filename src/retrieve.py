"""Build and query a persistent Chroma index for CloudServe documentation."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from chromadb.config import Settings


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")
os.environ.setdefault(
    "HF_HOME", str(PROJECT_ROOT / "storage" / "huggingface")
)
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


DEFAULT_DOCUMENTATION_PATH = PROJECT_ROOT / "data" / "documentation.json"
DEFAULT_CHROMA_PATH = PROJECT_ROOT / os.getenv("CHROMA_PATH", "storage/chroma")
COLLECTION_NAME = "cloudserve_documentation"


def load_documentation(path: str | Path = DEFAULT_DOCUMENTATION_PATH) -> list[Document]:
    """Read the supplied corpus and split articles into traceable passages."""
    source_path = Path(path)
    if not source_path.is_absolute():
        source_path = PROJECT_ROOT / source_path
    with source_path.open(encoding="utf-8") as file:
        articles: Any = json.load(file)

    if not isinstance(articles, list):
        raise ValueError("documentation.json must contain a list of articles")

    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=120)
    passages: list[Document] = []
    for article in articles:
        required = ("doc_id", "title", "content")
        if not all(article.get(field) for field in required):
            raise ValueError(f"Documentation article is missing one of {required}")

        metadata = {
            "doc_id": str(article["doc_id"]),
            "title": str(article["title"]),
            "category": str(article.get("category", "")),
        }
        applies_to = article.get("applies_to", [])
        if isinstance(applies_to, list):
            metadata["applies_to"] = ", ".join(str(item) for item in applies_to)

        passages.extend(
            Document(page_content=chunk, metadata=metadata.copy())
            for chunk in splitter.split_text(str(article["content"]))
            if chunk.strip()
        )

    if not passages:
        raise ValueError("No documentation passages were produced")
    return passages


def make_embeddings() -> HuggingFaceEmbeddings:
    """Create the local sentence-transformer embedding function."""
    model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


def get_vector_store(
    *,
    documentation_path: str | Path = DEFAULT_DOCUMENTATION_PATH,
    persist_directory: str | Path = DEFAULT_CHROMA_PATH,
) -> Chroma:
    """Load the existing index or create it once from the supplied corpus."""
    persist_path = Path(persist_directory)
    if not persist_path.is_absolute():
        persist_path = PROJECT_ROOT / persist_path
    persist_path.mkdir(parents=True, exist_ok=True)

    embeddings = make_embeddings()
    store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(persist_path),
        client_settings=Settings(anonymized_telemetry=False),
    )
    if store._collection.count() == 0:
        store.add_documents(load_documentation(documentation_path))
        # Chroma 0.4 persists automatically; this also supports versions where
        # explicit persistence is still required.
        persist = getattr(store, "persist", None)
        if callable(persist):
            persist()
    return store


def search_documentation(
    query: str, *, k: int | None = None, store: Chroma | None = None
) -> list[dict[str, Any]]:
    """Return passages with source identifiers suitable for citations."""
    if not query.strip():
        raise ValueError("query must not be empty")
    if store is None:
        store = get_vector_store()
    top_k = k or int(os.getenv("RETRIEVAL_TOP_K", "5"))
    results = store.similarity_search_with_score(query, k=top_k)
    return [
        {
            "doc_id": document.metadata.get("doc_id"),
            "title": document.metadata.get("title"),
            "passage": document.page_content,
            "distance": float(distance),
        }
        for document, distance in results
    ]
