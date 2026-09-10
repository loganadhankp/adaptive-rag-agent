from fastapi import FastAPI

from agents.llm_factory import get_vector_store
from backend.config import settings
from backend.database.connection import DatabaseManager
from backend.database.repository import Repository
from backend.routers.analytics import router as analytics_router
from backend.routers.chat import router as chat_router
from backend.routers.knowledge_base import router as kb_router
from backend.services.analytics_service import AnalyticsService
from backend.services.chat_service import ChatService
from backend.services.kb_service import KnowledgeBaseService

app = FastAPI(title="Adaptive RAG Agent")

try:
    vector_store = get_vector_store()
except Exception:
    vector_store = None

# Database init
# This keeps compatibility with code expecting a Repository class name in older project wiring.
db_manager = DatabaseManager(settings.SQLITE_DB_PATH)
db_manager.init_db()

app.state.settings = settings
app.state.db_manager = db_manager
app.state.repository = Repository(db_manager)
app.state.kb_service = KnowledgeBaseService(
    settings, app.state.repository, vector_store
)
app.state.chat_service = ChatService(settings, app.state.repository)
app.state.analytics_service = AnalyticsService(app.state.repository)

app.include_router(chat_router, prefix="/api/chat")
app.include_router(kb_router, prefix="/api/kb")
app.include_router(analytics_router, prefix="/api/analytics")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/metrics")
async def get_metrics():
    """Expose system and RAG analytics metrics."""
    return await app.state.analytics_service.get_summary()
