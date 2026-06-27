from app.db.models import Base
from app.db.session import engine
from app.utils.logging import logger


def init_database():
    logger.info("Initializing database...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully.")
