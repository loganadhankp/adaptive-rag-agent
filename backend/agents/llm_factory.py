import os

import chromadb
from langchain_anthropic import ChatAnthropic
from langchain_chroma import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from backend.config import get_settings


def get_llm(provider: str = None, model: str = None, temperature: float = 0.7):
    """Factory function to instantiate the configured production LLM."""
    settings = get_settings()
    if not provider or str(provider).strip().lower() in ["string", "none", "null", ""]:
        provider = getattr(settings, "LLM_PROVIDER", "gemini")
    provider = str(provider).strip().lower()

    if provider in ["gemini", "google"]:
        api_key = (
            os.environ.get("GOOGLE_API_KEY")
            or os.environ.get("GEMINI_API_KEY")
            or getattr(settings, "GOOGLE_API_KEY", "")
            or getattr(settings, "GEMINI_API_KEY", "")
        )
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY (or GEMINI_API_KEY) is not set. Please add your GOOGLE_API_KEY to the .env file or environment variables."
            )
        model_name = model or getattr(settings, "LLM_MODEL", "gemini-3.5-flash-lite")
        # Normalize deprecated or 404 Gemini models to active gemini-3.5-flash-lite
        if model_name in [
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite",
            "gemini-1.5-flash",
            "gemini-2.0-flash",
            "gemini-1.5-pro",
            "gemini-2.0-flash-exp",
            "gpt-4o-mini",
        ]:
            model_name = "gemini-3.5-flash-lite"
        return ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
            google_api_key=api_key,
        )
    elif provider == "openai":
        api_key = os.environ.get("OPENAI_API_KEY") or settings.OPENAI_API_KEY
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY is not set. Please add your OPENAI_API_KEY to the .env file or environment variables."
            )
        model_name = model or (
            settings.LLM_MODEL
            if "gpt" in settings.LLM_MODEL.lower()
            else "gpt-4o-mini"
        )
        return ChatOpenAI(
            model=model_name,
            temperature=temperature,
            openai_api_key=api_key,
        )
    elif provider == "anthropic":
        api_key = os.environ.get("ANTHROPIC_API_KEY") or settings.ANTHROPIC_API_KEY
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY is not set. Please add your ANTHROPIC_API_KEY to the .env file or environment variables."
            )
        return ChatAnthropic(
            model=model or "claude-sonnet-4-20250514",
            temperature=temperature,
            anthropic_api_key=api_key,
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


def get_embeddings():
    """Factory function to instantiate production text embeddings."""
    settings = get_settings()
    google_key = (
        os.environ.get("GOOGLE_API_KEY")
        or os.environ.get("GEMINI_API_KEY")
        or getattr(settings, "GOOGLE_API_KEY", "")
        or getattr(settings, "GEMINI_API_KEY", "")
    )
    openai_key = os.environ.get("OPENAI_API_KEY") or settings.OPENAI_API_KEY

    if google_key and (getattr(settings, "LLM_PROVIDER", "gemini") in ["gemini", "google"] or not openai_key):
        embedding_model = (
            settings.EMBEDDING_MODEL
            if "embedding" in settings.EMBEDDING_MODEL
            else "models/gemini-embedding-001"
        )
        if not embedding_model.startswith("models/") and "gemini" in embedding_model:
            embedding_model = f"models/{embedding_model}"
        return GoogleGenerativeAIEmbeddings(
            model=embedding_model,
            google_api_key=google_key,
        )
    elif openai_key:
        return OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL if "embedding" in settings.EMBEDDING_MODEL else "text-embedding-3-small",
            openai_api_key=openai_key,
        )
    else:
        raise ValueError(
            "Neither GOOGLE_API_KEY nor OPENAI_API_KEY is configured for document embeddings. Please set GOOGLE_API_KEY in your .env file."
        )


def get_vector_store():
    """Returns the Chroma vector store instance."""
    settings = get_settings()
    client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
    return Chroma(
        client=client,
        collection_name=settings.CHROMA_COLLECTION_NAME,
        embedding_function=get_embeddings(),
    )
