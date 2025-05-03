from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List
from datetime import datetime, timedelta
import os
import uuid
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
SECRET_KEY = "your-secret-key"  # Change this in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# In-memory database
fake_db = []
current_id = 1
notes_db = []
note_id_counter = 1

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Models
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

# Helper functions
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = next((u for u in fake_db if u["username"] == username), None)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# Endpoints
@app.post("/register")
async def register(user: User):
    if any(u["username"] == user.username for u in fake_db):
        raise HTTPException(status_code=400, detail="Username already exists")
    global current_id
    hashed_password = pwd_context.hash(user.password)
    fake_db.append({
        "id": current_id,
        "username": user.username,
        "hashed_password": hashed_password
    })
    current_id += 1
    return {"message": "User created successfully"}

@app.post("/login")
async def login(user: User):
    db_user = next((u for u in fake_db if u["username"] == user.username), None)
    if not db_user or not pwd_context.verify(user.password, db_user["hashed_password"]):
        raise HTTPException(401, "Invalid credentials")
    access_token = create_access_token(data={"sub": db_user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/notes", response_model=List[Note])
async def get_notes(current_user: dict = Depends(get_current_user)):
    return [n for n in notes_db if n["user_id"] == current_user["id"]]

@app.post("/notes", response_model=Note)
async def create_note(note: NoteCreate, current_user: dict = Depends(get_current_user)):
    global note_id_counter
    new_note = {
        "id": note_id_counter,
        "user_id": current_user["id"],
        **note.dict(),
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "files": []
    }
    notes_db.append(new_note)
    note_id_counter += 1
    return new_note

@app.put("/notes/{note_id}", response_model=Note)
async def update_note(note_id: int, note: NoteCreate, current_user: dict = Depends(get_current_user)):
    existing = next((n for n in notes_db if n["id"] == note_id and n["user_id"] == current_user["id"]), None)
    if not existing:
        raise HTTPException(404, "Note not found")
    existing.update({
        "title": note.title,
        "content": note.content,
        "updated_at": datetime.now()
    })
    return existing

@app.delete("/notes/{note_id}")
async def delete_note(note_id: int, current_user: dict = Depends(get_current_user)):
    global notes_db
    notes_db = [n for n in notes_db if not (n["id"] == note_id and n["user_id"] == current_user["id"])]
    return {"message": "Note deleted"}

@app.get("/notes/{note_id}", response_model=Note)
async def get_note(note_id: int, current_user: dict = Depends(get_current_user)):
    note = next((n for n in notes_db if n["id"] == note_id and n["user_id"] == current_user["id"]), None)
    if not note:
        raise HTTPException(404, "Note not found")
    return note

@app.post("/notes/{note_id}/files")
async def upload_file(note_id: int, file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    note = next((n for n in notes_db if n["id"] == note_id and n["user_id"] == current_user["id"]), None)
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
async def delete_file(file_id: str, note_id: int = Query(...), current_user: dict = Depends(get_current_user)):
    note = next((n for n in notes_db if n["id"] == note_id and n["user_id"] == current_user["id"]), None)
    if not note:
        raise HTTPException(404, "Note not found")
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

app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")