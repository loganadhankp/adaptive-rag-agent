from fastapi import APIRouter, Request

from backend.models import AnalyticsSummary

router = APIRouter()


@router.get("/summary", response_model=AnalyticsSummary)
async def get_summary(req: Request):
    """Get the analytics summary."""
    analytics_service = req.app.state.analytics_service
    return await analytics_service.get_summary()


@router.get("/metrics", response_model=AnalyticsSummary)
async def get_metrics(req: Request):
    """Get the system and RAG metrics."""
    analytics_service = req.app.state.analytics_service
    return await analytics_service.get_summary()
