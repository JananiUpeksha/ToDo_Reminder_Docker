import os
import smtplib
import time
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText

from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker


def get_secret(env_var_name: str, default: str = "") -> str:
    """Reads a value from a _FILE env var (Docker secret) if present,
    otherwise falls back to the plain env var, otherwise the default."""
    file_path = os.getenv(f"{env_var_name}_FILE")
    if file_path and os.path.exists(file_path):
        with open(file_path) as f:
            return f.read().strip()
    return os.getenv(env_var_name, default)


DB_USER = os.getenv("POSTGRES_USER", "todo_user")
DB_PASSWORD = get_secret("POSTGRES_PASSWORD", "todo_pass")
DB_HOST = os.getenv("POSTGRES_HOST", "db")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "todo_db")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Todo(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    due_at = Column(DateTime, nullable=False)
    is_completed = Column(Boolean, default=False)
    reminder_sent = Column(Boolean, default=False)


SMTP_HOST = os.getenv("MAILTRAP_HOST", "sandbox.smtp.mailtrap.io")
SMTP_PORT = int(os.getenv("MAILTRAP_PORT", "2525"))
SMTP_USER = os.getenv("MAILTRAP_USER", "")
SMTP_PASSWORD = os.getenv("MAILTRAP_PASSWORD", "")

CHECK_INTERVAL_SECONDS = 60
REMINDER_WINDOW_MINUTES = 5


def send_reminder_email(todo: Todo):
    subject = f"Reminder: '{todo.title}' is due soon"
    body = (
        f"Your to-do '{todo.title}' is due at {todo.due_at}.\n\n"
        f"Description: {todo.description or 'No description provided.'}"
    )

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = "reminders@todo-app.local"
    msg["To"] = "user@todo-app.local"

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)

    print(f"[worker] Sent reminder email for todo id={todo.id} ('{todo.title}')")


def check_and_send_reminders():
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        window_end = now + timedelta(minutes=REMINDER_WINDOW_MINUTES)

        due_soon_todos = (
            db.query(Todo)
            .filter(
                Todo.reminder_sent == False,  # noqa: E712
                Todo.is_completed == False,
                Todo.due_at <= window_end,
                Todo.due_at >= now,
            )
            .all()
        )

        for todo in due_soon_todos:
            try:
                send_reminder_email(todo)
                todo.reminder_sent = True
                db.commit()
            except Exception as e:
                print(f"[worker] Failed to send reminder for todo id={todo.id}: {e}")
                db.rollback()

        if not due_soon_todos:
            print(f"[worker] No reminders due at {now.isoformat()}")

    finally:
        db.close()


if __name__ == "__main__":
    print("[worker] Starting reminder worker loop...")
    print(f"[worker] Checking every {CHECK_INTERVAL_SECONDS}s, "
          f"window: {REMINDER_WINDOW_MINUTES} min before due_at")

    while True:
        check_and_send_reminders()
        time.sleep(CHECK_INTERVAL_SECONDS)