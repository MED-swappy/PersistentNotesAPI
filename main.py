import os
from fastapi import FastAPI, Depends, status, HTTPException
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, Session
from sqlalchemy import create_engine, String , Text, Integer , DateTime
from datetime import datetime
from typing import Annotated
from pydantic import BaseModel


DATABASE_URL = "os.environ["DATABASE_URL"]"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine, autoflush=False , autocommit=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app  = FastAPI()

class NoteCreate(BaseModel):
    title : str
    content : str | None = None

class NoteUpdate(BaseModel):
    title: str | None = None
    content: str | None = None


class Base(DeclarativeBase):
    pass


class Note(Base):
    __tablename__= "notes"
    id : Mapped[int] = mapped_column(Integer , primary_key=True, autoincrement=True)
    title : Mapped[str] = mapped_column(String(100), nullable=False)
    content : Mapped[str | None] = mapped_column(Text , nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    def __repr__(self) -> str:
        return f"<Note id = {self.id},Note title = {self.title!r}"


Base.metadata.create_all(engine)



@app.get("/")
def root():
    return {"message" : "Welcome to my persistent notes api"}

@app.get("/notes")
def get_notes(db: Annotated[Session, Depends(get_db)]):
    notes = db.query(Note).all()
    return notes


@app.post("/notes", status_code=status.HTTP_201_CREATED)
def post_notes(note: NoteCreate, db: Annotated[Session, Depends(get_db)]):
    new_note = Note(title = note.title, content = note.content)
    db.add(new_note)
    db.commit()
    db.refresh(new_note)
    return new_note

@app.get("/notes/{note_id}")
def get_note_id(note_id: int, db: Annotated[Session, Depends(get_db)]):
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note

@app.put("/notes/{note_id}")
def update_note(note_id: int, note_data: NoteUpdate, db: Annotated[Session, Depends(get_db)]):
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")

    if note_data.title is not None:
        note.title = note_data.title
    if note_data.content is not None:
        note.content = note_data.content

    db.commit()
    db.refresh(note)
    return note

@app.delete("/notes/{note_id}", status_code=204)
def delete_note(note_id: int, db: Annotated[Session, Depends(get_db)]):
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    db.delete(note)
    db.commit()