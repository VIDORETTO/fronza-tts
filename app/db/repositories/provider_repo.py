from app.db.models import ApiKey, Provider
from app.db.session import get_session
from app.utils.logging import logger
from app.utils.security import decrypt_value, mask_api_key


class ProviderRepo:
    def list_all(self) -> list[Provider]:
        with get_session() as session:
            return session.query(Provider).all()

    def get(self, provider_id: str) -> Provider | None:
        with get_session() as session:
            return session.query(Provider).filter(Provider.id == provider_id).first()

    def upsert(self, provider: Provider) -> Provider:
        with get_session() as session:
            existing = session.query(Provider).filter(Provider.id == provider.id).first()
            if existing:
                for key, value in provider.__dict__.items():
                    if key != "_sa_instance_state":
                        setattr(existing, key, value)
                session.commit()
                return existing
            session.add(provider)
            session.commit()
            return provider

    def set_status(self, provider_id: str, status: str, error: str | None = None) -> None:
        with get_session() as session:
            prov = session.query(Provider).filter(Provider.id == provider_id).first()
            if prov:
                prov.status = status
                if error:
                    prov.last_error = error
                session.commit()


class ApiKeyRepo:
    def get_by_provider(self, provider_id: str) -> list[ApiKey]:
        with get_session() as session:
            return session.query(ApiKey).filter(ApiKey.provider_id == provider_id).all()

    def get_decrypted(self, provider_id: str, is_admin: bool = False) -> str | None:
        with get_session() as session:
            q = session.query(ApiKey).filter(
                ApiKey.provider_id == provider_id,
                ApiKey.is_admin_key == is_admin,
            )
            key = q.first()
            if key:
                return decrypt_value(key.encrypted_value)
            return None

    def has_key(self, provider_id: str) -> bool:
        with get_session() as session:
            return session.query(ApiKey).filter(ApiKey.provider_id == provider_id).count() > 0

    def save(self, provider_id: str, encrypted_value: str, key_name: str = "default", is_admin: bool = False) -> ApiKey:
        with get_session() as session:
            key = ApiKey(
                provider_id=provider_id,
                key_name=key_name,
                encrypted_value=encrypted_value,
                is_admin_key=is_admin,
            )
            session.add(key)
            session.commit()
            return key

    def delete(self, provider_id: str) -> None:
        with get_session() as session:
            session.query(ApiKey).filter(ApiKey.provider_id == provider_id).delete()
            session.commit()
