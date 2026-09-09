import logging

from src.config import settings


def configure_logging() -> None:
    """Sets up root logging config once, at app startup."""
    logging.basicConfig(
        level=settings.LOG_LEVEL,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
