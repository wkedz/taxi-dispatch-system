from collections.abc import Iterator

from sqlalchemy.orm import Session

from dispatcher_service.app.adapters.database import SessionLocal


def get_db_session() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
