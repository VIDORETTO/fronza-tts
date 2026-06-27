from datetime import datetime

from app.db.models import Generation, UsageLedger
from app.db.session import get_session
from app.utils.logging import logger


class GenerationRepo:
    def list_all(self, limit: int = 100) -> list[Generation]:
        with get_session() as session:
            return session.query(Generation).order_by(Generation.created_at.desc()).limit(limit).all()

    def get(self, generation_id: str) -> Generation | None:
        with get_session() as session:
            return session.query(Generation).filter(Generation.id == generation_id).first()

    def save(self, generation: Generation) -> Generation:
        with get_session() as session:
            session.add(generation)
            session.commit()
            return generation

    def delete(self, generation_id: str) -> None:
        with get_session() as session:
            session.query(Generation).filter(Generation.id == generation_id).delete()
            session.commit()


class UsageRepo:
    def list_by_provider(self, provider_id: str, limit: int = 100) -> list[UsageLedger]:
        with get_session() as session:
            return (
                session.query(UsageLedger)
                .filter(UsageLedger.provider_id == provider_id)
                .order_by(UsageLedger.created_at.desc())
                .limit(limit)
                .all()
            )

    def total_by_provider(self, provider_id: str) -> float:
        with get_session() as session:
            result = (
                session.query(UsageLedger.actual_used)
                .filter(UsageLedger.provider_id == provider_id)
                .all()
            )
            return sum(r[0] for r in result if r[0] is not None)

    def record(self, entry: UsageLedger) -> UsageLedger:
        with get_session() as session:
            session.add(entry)
            session.commit()
            return entry
