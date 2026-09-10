from backend.models import AnalyticsSummary


class AnalyticsService:
    def __init__(self, repository):
        self.repository = repository

    async def get_summary(self) -> AnalyticsSummary:
        """Retrieves the analytics summary from the repository."""
        data = self.repository.get_analytics_summary()
        return AnalyticsSummary(**data)
