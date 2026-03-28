"""Session and transaction helpers for storage backends."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


class StorageSessionManager:
    """Create SQLAlchemy sessions and enforce transactional boundaries."""

    def __init__(self, dsn: str) -> None:
        self._engine: Engine = create_engine(dsn, future=True)
        self._session_factory = sessionmaker(
            bind=self._engine,
            autoflush=False,
            expire_on_commit=False,
            class_=Session,
        )

    @property
    def engine(self) -> Engine:
        """Expose the underlying engine for setup and diagnostics."""
        return self._engine

    @contextmanager
    def session_scope(self) -> Iterator[Session]:
        """Yield a session that commits on success and rolls back on failure."""
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
