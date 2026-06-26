import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


def get_secret(env_var_name: str, default: str = "") -> str:
    """Reads a value from a _FILE env var (Docker secret) if present,
    otherwise falls back to the plain env var, otherwise the default.
    This lets the same code work whether secrets are used or not."""
    file_path = os.getenv(f"{env_var_name}_FILE")
    if file_path and os.path.exists(file_path):
        with open(file_path) as f:
            return f.read().strip()
    return os.getenv(env_var_name, default)


DB_USER = os.getenv("POSTGRES_USER", "todo_user")
DB_PASSWORD = get_secret("POSTGRES_PASSWORD", "todo_pass")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "todo_db")

SQLALCHEMY_DATABASE_URL = (
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()