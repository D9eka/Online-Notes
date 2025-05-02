from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List
from datetime import datetime

app = FastAPI()

# Разрешаем все CORS запросы для простоты
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Временное хранилище данных в памяти
fake_db = []
current_id = 1
notes_db = []
note_id_counter = 1


# Модели данных
class User(BaseModel):
    username: str
    password: str


class UserResponse(User):
    id: int

    title: str
    content: str


class NoteCreate(NoteBase):
    pass


class Note(NoteBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime


# Регистрация
@app.post("/register")
async def register(user: User):
    global current_id
    if any(u["username"] == user.username for u in fake_db):
        raise HTTPException(status_code=400, detail="Username already exists")

    new_user = {
        "id": current_id,
        "username": user.username,
        "password": user.password
    }
    fake_db.append(new_user)
    current_id += 1
    return {"message": "User created successfully"}


# Авторизация
@app.post("/login")
async def login(user: User):
    user_exists = next(
        (u for u in fake_db
         if u["username"] == user.username
         and u["password"] == user.password),
        None
    )
    if not user_exists:
        raise HTTPException(401, "Invalid credentials")
    return {"message": "Login successful"}

# Заметки
@app.get("/notes", response_model=List[Note])
async def get_notes(
        username: str = Query(...),
        password: str = Query(...)
):
    user = next(
        (u for u in fake_db
         if u["username"] == username
         and u["password"] == password),
        None
    )
    if not user:
        raise HTTPException(401, "Invalid credentials")

    return [n for n in notes_db if n["user_id"] == user["id"]]


@app.post("/notes", response_model=Note)
async def create_note(
        note: NoteCreate,
        username: str = Query(...),
        password: str = Query(...)
):
    user = next(
        (u for u in fake_db
         if u["username"] == username
         and u["password"] == password),
        None
    )
    if not user:
        raise HTTPException(401, "Invalid credentials")

    global note_id_counter
    new_note = {
        "id": note_id_counter,
        "user_id": user["id"],
        "title": note.title,
        "content": note.content,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    notes_db.append(new_note)
    note_id_counter += 1
    return new_note


@app.put("/notes/{note_id}", response_model=Note)
async def update_note(
        note_id: int,
        note: NoteCreate,
        username: str = Query(...),
        password: str = Query(...)
):
    user = next(
        (u for u in fake_db
         if u["username"] == username
         and u["password"] == password),
        None
    )
    if not user:
        raise HTTPException(401, "Invalid credentials")

    existing = next(
        (n for n in notes_db
         if n["id"] == note_id
         and n["user_id"] == user["id"]),
        None
    )
    if not existing:
        raise HTTPException(404, "Note not found")

    existing["title"] = note.title
    existing["content"] = note.content
    existing["updated_at"] = datetime.now()
    return existing


@app.delete("/notes/{note_id}")
async def delete_note(
        note_id: int,
        username: str = Query(...),
        password: str = Query(...)
):
    user = next(
        (u for u in fake_db
         if u["username"] == username
         and u["password"] == password),
        None
    )
    if not user:
        raise HTTPException(401, "Invalid credentials")

    global notes_db
    notes_db = [
        n for n in notes_db
        if not (n["id"] == note_id
                and n["user_id"] == user["id"])
    ]
    return {"message": "Note deleted"}


# Отдаем статические файлы фронтенда
app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")