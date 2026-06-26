import json
import os
from typing import List

import redis
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from . import models, schemas
from .database import Base, SessionLocal, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="To-Do Reminder API")

# --- Redis setup ---
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
CACHE_KEY = "todos:all"
CACHE_TTL_SECONDS = 30  # short TTL - just enough to absorb repeated reads, not so long that staleness matters

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


def invalidate_todos_cache():
    """Call this after any write (create/update/delete/complete) so stale
    list data is never served. Deleting the key is simpler and safer than
    trying to update it in place."""
    redis_client.delete(CACHE_KEY)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def root():
    return {"message": "To-Do Reminder API is running"}


@app.post("/todos", response_model=schemas.TodoResponse, status_code=201)
def create_todo(todo: schemas.TodoCreate, db: Session = Depends(get_db)):
    db_todo = models.Todo(**todo.model_dump())
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    invalidate_todos_cache()
    return db_todo


@app.get("/todos", response_model=List[schemas.TodoResponse])
def list_todos(db: Session = Depends(get_db)):
    # 1. Try the cache first
    cached = redis_client.get(CACHE_KEY)
    if cached:
        return json.loads(cached)

    # 2. Cache miss - query Postgres
    todos = db.query(models.Todo).all()
    result = [schemas.TodoResponse.model_validate(t).model_dump(mode="json") for t in todos]

    # 3. Store in cache for next time
    redis_client.set(CACHE_KEY, json.dumps(result), ex=CACHE_TTL_SECONDS)

    return result


@app.get("/todos/{todo_id}", response_model=schemas.TodoResponse)
def get_todo(todo_id: int, db: Session = Depends(get_db)):
    db_todo = db.query(models.Todo).filter(models.Todo.id == todo_id).first()
    if not db_todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return db_todo


@app.put("/todos/{todo_id}", response_model=schemas.TodoResponse)
def update_todo(todo_id: int, todo: schemas.TodoUpdate, db: Session = Depends(get_db)):
    db_todo = db.query(models.Todo).filter(models.Todo.id == todo_id).first()
    if not db_todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    update_data = todo.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_todo, key, value)

    db.commit()
    db.refresh(db_todo)
    invalidate_todos_cache()
    return db_todo


@app.delete("/todos/{todo_id}", status_code=204)
def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    db_todo = db.query(models.Todo).filter(models.Todo.id == todo_id).first()
    if not db_todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    db.delete(db_todo)
    db.commit()
    invalidate_todos_cache()
    return None


@app.patch("/todos/{todo_id}/complete", response_model=schemas.TodoResponse)
def mark_complete(todo_id: int, db: Session = Depends(get_db)):
    db_todo = db.query(models.Todo).filter(models.Todo.id == todo_id).first()
    if not db_todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    db_todo.is_completed = True
    db.commit()
    db.refresh(db_todo)
    invalidate_todos_cache()
    return db_todo