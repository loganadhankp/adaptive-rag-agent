import logging
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from backend.agents.llm_factory import get_llm
from backend.workflow.state import RAGState

logger = logging.getLogger(__name__)

GENERAL_CHAT_SYSTEM_PROMPT = (
    "You are a helpful, intelligent, polite, and precise AI assistant. "
    "Answer the user's questions clearly, accurately, and naturally. "
    "For conceptual questions, programming questions, coding help (such as Python, FastAPI, OOP, recursion), "
    "provide direct, well-structured, formatted responses with markdown. "
    "For greetings or casual conversation, respond warmly and helpfully. "
    "Do NOT mention knowledge bases, document sufficiency, or retrieval, as this is a general conversational interaction."
)


def generate_general_chat(state: RAGState) -> dict:
    """Answers general conversational or knowledge queries directly using the LLM without retrieval."""
    question = state.get("question", "")
    logger.info(f"[GeneralChatNode] Generating direct conversational response for: '{question}'")

    try:
        llm = get_llm(
            provider=state.get("provider"),
            model=state.get("model"),
            temperature=state.get("temperature", 0.7),
        )

        messages = [SystemMessage(content=GENERAL_CHAT_SYSTEM_PROMPT)]

        # Append past conversation history (limit to last 10 messages for context)
        raw_history = state.get("conversation_history", [])[-10:]
        for msg in raw_history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if not content:
                continue
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))

        # Add current question
        messages.append(HumanMessage(content=question))

        response = llm.invoke(messages)
        raw_content = response.content if hasattr(response, "content") else response
        if isinstance(raw_content, list):
            parts = []
            for p in raw_content:
                if isinstance(p, dict) and "text" in p:
                    parts.append(p["text"])
                else:
                    parts.append(str(p))
            generation_text = "".join(parts)
        else:
            generation_text = str(raw_content)

        return {
            "generation": generation_text,
            "answerability_status": "GENERAL_CHAT",
            "query_route": "GENERAL_CHAT",
            "is_fully_answerable": True,
            "documents": [],
            "sources": [],
            "relevance_score": 100,
            "coverage_score": 100,
            "knowledge_gap_reason": "NONE",
            "available_information": "",
            "missing_information": [],
            "clarification_request": "",
            "context_assessment": None,
            "workflow_steps": [
                {
                    "step": "general_chat",
                    "status": "completed",
                    "detail": "Direct conversational response generated",
                }
            ],
            "current_step": "general_chat",
        }
    except Exception as e:
        logger.error(f"[GeneralChatNode] Direct response failed: {e}", exc_info=True)
        return {
            "generation": f"I'm sorry, I encountered an issue generating a response: {e}",
            "answerability_status": "GENERAL_CHAT",
            "query_route": "GENERAL_CHAT",
            "error": str(e),
            "documents": [],
            "sources": [],
            "workflow_steps": [
                {
                    "step": "general_chat",
                    "status": "failed",
                    "detail": f"Error: {e}",
                }
            ],
            "current_step": "general_chat",
        }
