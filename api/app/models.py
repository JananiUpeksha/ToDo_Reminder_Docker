from sqlalchemy import Boolean, Column, DateTime, Integer, String
from .database import Base


class Todo(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    due_at = Column(DateTime, nullable=False)
    is_completed = Column(Boolean, default=False)
    reminder_sent = Column(Boolean, default=False)
