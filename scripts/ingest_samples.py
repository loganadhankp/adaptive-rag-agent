from pathlib import Path

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from agents.llm_factory import get_vector_store
from backend.config import get_settings


def ingest_file(path: Path):
    settings = get_settings()
    vs = get_vector_store()

    loader = TextLoader(str(path))
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE, chunk_overlap=settings.CHUNK_OVERLAP
    )
    splits = splitter.split_documents(docs)

    for i, s in enumerate(splits):
        s.metadata.update(
            {
                "source": path.name,
                "document_id": f"sample_{path.stem}",
                "chunk_id": f"sample_{path.stem}_chunk_{i}",
            }
        )

    if vs:
        print(f"Adding {len(splits)} chunks to vector store...")
        vs.add_documents(splits)
        print("Ingestion complete.")
    else:
        print("No vector store available. Skipping ingestion.")


if __name__ == "__main__":
    sample = Path("data/sample/company_handbook.txt")
    if not sample.exists():
        print(f"Sample file not found at {sample}")
    else:
        ingest_file(sample)
