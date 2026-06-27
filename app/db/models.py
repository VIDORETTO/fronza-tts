from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, create_engine,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Provider(Base):
    __tablename__ = "providers"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    enabled = Column(Boolean, nullable=False, default=True)
    priority = Column(Integer, nullable=False)
    free_only = Column(Boolean, nullable=False, default=True)
    status = Column(String, nullable=False, default="unknown")
    reset_policy = Column(String, nullable=False, default="unknown")
    quota_source = Column(String, nullable=False, default="unknown")
    last_error = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider_id = Column(String, nullable=False)
    key_name = Column(String, nullable=False)
    encrypted_value = Column(String, nullable=False)
    is_admin_key = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class QuotaSnapshot(Base):
    __tablename__ = "quota_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider_id = Column(String, nullable=False)
    unit = Column(String, nullable=False)
    used = Column(Float, nullable=True)
    limit_value = Column(Float, nullable=True)
    remaining = Column(Float, nullable=True)
    reset_policy = Column(String, nullable=False)
    reset_at = Column(DateTime, nullable=True)
    source = Column(String, nullable=False)
    confidence = Column(String, nullable=False)
    raw_response_json = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class ManualBalance(Base):
    __tablename__ = "manual_balances"

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider_id = Column(String, nullable=False)
    unit = Column(String, nullable=False)
    balance = Column(Float, nullable=False)
    note = Column(String, nullable=True)
    valid_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class UsageLedger(Base):
    __tablename__ = "usage_ledger"

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider_id = Column(String, nullable=False)
    model_id = Column(String, nullable=True)
    voice_id = Column(String, nullable=True)
    language = Column(String, nullable=True)
    text_hash = Column(String, nullable=False)
    characters = Column(Integer, nullable=False)
    estimated_tokens = Column(Integer, nullable=True)
    estimated_seconds = Column(Float, nullable=True)
    actual_unit = Column(String, nullable=True)
    actual_used = Column(Float, nullable=True)
    source = Column(String, nullable=False)
    generation_id = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class Generation(Base):
    __tablename__ = "generations"

    id = Column(String, primary_key=True)
    provider_id = Column(String, nullable=False)
    model_id = Column(String, nullable=True)
    voice_id = Column(String, nullable=True)
    language = Column(String, nullable=True)
    input_text = Column(Text, nullable=False)
    input_characters = Column(Integer, nullable=False)
    output_file_path = Column(String, nullable=False)
    output_format = Column(String, nullable=False)
    duration_seconds = Column(Float, nullable=True)
    status = Column(String, nullable=False)
    error_message = Column(String, nullable=True)
    fallback_from = Column(String, nullable=True)
    fallback_chain = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class FallbackEvent(Base):
    __tablename__ = "fallback_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    generation_id = Column(String, nullable=True)
    from_provider = Column(String, nullable=True)
    to_provider = Column(String, nullable=True)
    reason = Column(String, nullable=False)
    error_code = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
