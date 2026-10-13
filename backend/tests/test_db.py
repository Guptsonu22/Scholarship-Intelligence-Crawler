from sqlalchemy import text
from app.db.database import SessionLocal, engine
from app.db.init_db import init_db, SystemInfo


def test_database_connection():
    """Verify that a session can execute queries against SQLite."""
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT 1")).scalar()
        assert result == 1
    finally:
        db.close()


def test_database_schema_initialization():
    """Verify that init_db creates tables and model CRUD works."""
    init_db()
    db = SessionLocal()
    try:
        # Check writing and reading to SystemInfo table
        record = db.query(SystemInfo).filter_by(key="test_key").first()
        if not record:
            record = SystemInfo(key="test_key", value="test_value")
            db.add(record)
            db.commit()
            db.refresh(record)

        assert record.id is not None
        assert record.key == "test_key"
        assert record.value == "test_value"

        # Cleanup test record
        db.delete(record)
        db.commit()
    finally:
        db.close()
