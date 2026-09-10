# flake8: noqa - prompt templates intentionally contain long lines
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field


class RewrittenQuery(BaseModel):
    """Rewritten query for improved retrieval."""

    rewritten_query: str = Field(description="The improved, more specific query")
    reasoning: str = Field(description="Why the query was rewritten this way")


REWRITING_SYSTEM_PROMPT = """You are an expert search query optimizer.
Your task is to rewrite a given user question to optimize search retrieval.

CRITICAL RULES:
1. Base your rewrite STRICTLY on the original user question and prior conversation history (for resolving pronouns or vague references).
2. DO NOT use, incorporate, or extrapolate from any unrelated, irrelevant, or external content.
3. NEVER alter the core topic or intent of the user's inquiry.
4. If the question is already clear, retain the original query or make minimal necessary phrasing improvements.
5. Never generate search queries based on unrelated retrieved content."""

REWRITING_HUMAN_PROMPT = """Conversation History:
{conversation_history}

Original Question: {question}"""

REWRITING_PROMPT = ChatPromptTemplate.from_messages(
    [("system", REWRITING_SYSTEM_PROMPT), ("human", REWRITING_HUMAN_PROMPT)]
)

