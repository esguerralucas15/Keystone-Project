from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base, Session


DATABASE_URL = "sqlite:///./equifinance.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()


def ensure_schema():
    with engine.begin() as conn:
        table = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='daily_records'")
        ).fetchone()
        if not table:
            return

        columns = {
            row[1]
            for row in conn.execute(text("PRAGMA table_info(daily_records)")).fetchall()
        }
        if "expense_type" not in columns:
            conn.execute(text("ALTER TABLE daily_records ADD COLUMN expense_type VARCHAR"))
            conn.execute(text("UPDATE daily_records SET expense_type = 'variable' WHERE expense_type IS NULL"))

