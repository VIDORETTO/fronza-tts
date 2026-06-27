from app.db.models import ManualBalance, QuotaSnapshot
from app.db.session import get_session


class QuotaRepo:
    def get_latest_snapshot(self, provider_id: str) -> QuotaSnapshot | None:
        with get_session() as session:
            return (
                session.query(QuotaSnapshot)
                .filter(QuotaSnapshot.provider_id == provider_id)
                .order_by(QuotaSnapshot.created_at.desc())
                .first()
            )

    def save_snapshot(self, snapshot: QuotaSnapshot) -> QuotaSnapshot:
        with get_session() as session:
            session.add(snapshot)
            session.commit()
            return snapshot

    def get_manual_balance(self, provider_id: str) -> ManualBalance | None:
        with get_session() as session:
            return (
                session.query(ManualBalance)
                .filter(ManualBalance.provider_id == provider_id)
                .order_by(ManualBalance.created_at.desc())
                .first()
            )

    def save_manual_balance(self, balance: ManualBalance) -> ManualBalance:
        with get_session() as session:
            session.add(balance)
            session.commit()
            return balance
