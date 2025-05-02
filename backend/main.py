from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List
from datetime import datetime
import os
import uuid

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
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# Модели данных
class User(BaseModel):
    username: str
    password: str


class NoteBase(BaseModel):
    title: str
    content: str


class NoteCreate(NoteBase):
    pass


class FileInfo(BaseModel):
    id: str
    name: str
    path: str


class Note(NoteBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    files: List[FileInfo] = []


# Регистрация
@app.post("/register")
async def register(user: User):
    if any(u["username"] == user.username for u in fake_db):
        raise HTTPException(status_code=400, detail="Username already exists")

    global current_id
    fake_db.append({
        "id": current_id,
        "username": user.username,
        "password": user.password
    })
    current_id += 1
    return {"message": "User created successfully"}


# Авторизация
@app.post("/login")
async def login(user: User):
    if not next((u for u in fake_db if u["username"] == user.username and u["password"] == user.password), None):
        raise HTTPException(401, "Invalid credentials")
    return {"message": "Login successful"}

# Заметки
@app.get("/notes", response_model=List[Note])
async def get_notes(username: str = Query(...), password: str = Query(...)):
    user = next((u for u in fake_db if u["username"] == username and u["password"] == password), None)
    if not user:
        raise HTTPException(401, "Invalid credentials")
    return [n for n in notes_db if n["user_id"] == user["id"]]


@app.post("/notes", response_model=Note)
async def create_note(note: NoteCreate, username: str = Query(...), password: str = Query(...)):
    user = next((u for u in fake_db if u["username"] == username and u["password"] == password), None)
    if not user:
        raise HTTPException(401, "Invalid credentials")

    global note_id_counter
    new_note = {
        "id": note_id_counter,
        "user_id": user["id"],
        **note.dict(),
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "files": []
    }
    notes_db.append(new_note)
    note_id_counter += 1
    return new_note


@app.put("/notes/{note_id}", response_model=Note)
async def update_note(note_id: int, note: NoteCreate, username: str = Query(...), password: str = Query(...)):
    user = next((u for u in fake_db if u["username"] == username and u["password"] == password), None)
    existing = next((n for n in notes_db if n["id"] == note_id and n["user_id"] == user["id"]), None)

    if not user or not existing:
        raise HTTPException(404, "Note not found")

    existing.update({
        "title": note.title,
        "content": note.content,
        "updated_at": datetime.now()
    })
    return existing


@app.delete("/notes/{note_id}")
async def delete_note(note_id: int, username: str = Query(...), password: str = Query(...)):
    user = next((u for u in fake_db if u["username"] == username and u["password"] == password), None)
    if user:
        global notes_db
        notes_db = [n for n in notes_db if not (n["id"] == note_id and n["user_id"] == user["id"])]
    return {"message": "Note deleted"}


# Файлы
@app.post("/notes/{note_id}/files")
async def upload_file(note_id: int, file: UploadFile = File(...), username: str = Query(...),
                      password: str = Query(...)):
    user = next((u for u in fake_db if u["username"] == username and u["password"] == password), None)
    note = next((n for n in notes_db if n["id"] == note_id and n["user_id"] == user["id"]), None)

    if not note:
        raise HTTPException(404, "Note not found")

    file_id = str(uuid.uuid4())
    filename = f"{file_id}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as f:
        f.write(await file.read())

    note["files"].append({
        "id": file_id,
        "name": file.filename,
        "path": filename
    })
    return {"id": file_id, "name": file.filename}


@app.delete("/files/{file_id}")
async def delete_file(file_id: str, note_id: int = Query(...)):
    note = next((n for n in notes_db if n["id"] == note_id), None)
    if note:
        file_info = next((f for f in note["files"] if f["id"] == file_id), None)
        if file_info:
            os.remove(os.path.join(UPLOAD_DIR, file_info["path"]))
            note["files"] = [f for f in note["files"] if f["id"] != file_id]
    return {"message": "File deleted"}


@app.get("/files/{filename}")
async def get_file(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(404, "File not found")
    return FileResponse(file_path)

# Отдаем статические файлы фронтенда
app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")