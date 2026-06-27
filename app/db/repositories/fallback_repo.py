from app.db.models import FallbackEvent
from app.db.session import get_session


class FallbackRepo:
    def list_by_generation(self, generation_id: str) -> list[FallbackEvent]:
        with get_session() as session:
            return (
                session.query(FallbackEvent)
                .filter(FallbackEvent.generation_id == generation_id)
                .order_by(FallbackEvent.created_at.asc())
                .all()
            )

    def record(self, event: FallbackEvent) -> FallbackEvent:
        with get_session() as session:
            session.add(event)
            session.commit()
            return event
