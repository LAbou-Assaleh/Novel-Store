from __future__ import annotations

import json
import os
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import urlsplit, urlunsplit

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

try:
    from .models import Base
except ImportError:
    from models import Base


CONFIG_PATH = Path(__file__).resolve().parent / ".nks_config.json"
DATABASE_URL_ENV = "NKS_DATABASE_URL"


def redact_database_url(database_url: str) -> str:
    """Return a database URL with any password removed from display output."""
    if not database_url.strip():
        return database_url

    parts = urlsplit(database_url)
    if not parts.netloc or "@" not in parts.netloc:
        return database_url

    userinfo, hostinfo = parts.netloc.rsplit("@", 1)
    if ":" not in userinfo:
        return database_url

    username, _password = userinfo.split(":", 1)
    redacted_netloc = f"{username}:***@{hostinfo}"
    return urlunsplit((parts.scheme, redacted_netloc, parts.path, parts.query, parts.fragment))


def write_config(database_url: str) -> dict[str, str]:
    """Persist the selected database URL for future CLI commands."""
    config = {"database_url": database_url.strip()}
    CONFIG_PATH.write_text(json.dumps(config, indent=2), encoding="utf-8")
    return config


def read_config() -> dict[str, Any]:
    """Load CLI configuration from disk when available."""
    if not CONFIG_PATH.exists():
        return {}
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def resolve_database_url(database_url: str | None = None, require_config: bool = True) -> str:
    """Resolve the active database URL from an explicit value or saved config."""
    if database_url and database_url.strip():
        return database_url.strip()

    env_database_url = os.getenv(DATABASE_URL_ENV, "").strip()
    if env_database_url:
        return env_database_url

    config = read_config()
    stored = str(config.get("database_url", "")).strip()
    if stored:
        return stored

    raise RuntimeError(
        "Database URL is not configured. Use --db, set NKS_DATABASE_URL, or create the gitignored local config."
    )


@lru_cache(maxsize=8)
def get_engine(database_url: str) -> Engine:
    """Build and cache an engine for a database URL."""
    return create_engine(database_url, future=True)


def get_session_factory(database_url: str | None = None):
    """Create a session factory for the resolved database URL."""
    resolved_url = resolve_database_url(database_url)
    return sessionmaker(
        bind=get_engine(resolved_url),
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        future=True,
    )


def init_db(database_url: str | None = None) -> str:
    """Create all schema objects for the resolved database."""
    resolved_url = resolve_database_url(database_url, require_config=False)
    Base.metadata.create_all(bind=get_engine(resolved_url))
    return resolved_url


@contextmanager
def get_session(database_url: str | None = None) -> Iterator[Session]:
    """Provide a transactional SQLAlchemy session."""
    session = get_session_factory(database_url)()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
