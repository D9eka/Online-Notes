import os
from typing import List
from fastapi import FastAPI, HTTPException, Depends, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import RedirectResponse

from backend.storage import storage
from backend.database import engine, get_db
from backend.base import Base
import backend.crud as crud
import backend.models as models
from backend.schemas import Token, NoteCreate, NoteOut, FileInfo
from backend.auth import authenticate_user, create_access_token, get_current_user

app = FastAPI()

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")

@app.post("/signup", response_model=Token)
async def signup(form_data: OAuth2PasswordRequestForm = Depends(), session: AsyncSession = Depends(get_db)):
    user = await crud.get_user_by_username(session, form_data.username)
    if user:
        raise HTTPException(status_code=400, detail="Username already registered")
    new_user = await crud.create_user(session, form_data.username, form_data.password)
    access_token = create_access_token({"sub": new_user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), session: AsyncSession = Depends(get_db)):
    user = await authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token({"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/notes", response_model=List[NoteOut])
async def list_notes(current_user: models.User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    return await crud.get_notes_for_user(session, current_user.id)

@app.post("/notes", response_model=NoteOut)
async def create_new_note(
    note_data: NoteCreate,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    new_note = await crud.create_note(
        session=db,
        user_id=current_user.id,
        title=note_data.title,
        content=note_data.content
    )
    return new_note

@app.get("/notes/{note_id}", response_model=NoteOut)
async def get_note(
    note_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    note = await crud.get_note_by_id(db, note_id, current_user.id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note

@app.put("/notes/{note_id}", response_model=NoteOut)
async def update_existing_note(note_id: int, note_in: NoteCreate, current_user: models.User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    note = await crud.get_note_by_id(session, note_id, current_user.id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return await crud.update_note(session, note, note_in.title, note_in.content)

@app.delete("/notes/{note_id}")
async def remove_note(note_id: int, current_user: models.User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    note = await crud.get_note_by_id(session, note_id, current_user.id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    await crud.delete_note(session, note)
    return {"message": "Note deleted"}

@app.post("/notes/{note_id}/files", response_model=FileInfo)
async def upload_note_file(note_id: int, file: UploadFile = File(...), current_user: models.User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    note = await crud.get_note_by_id(session, note_id, current_user.id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    file_obj = await crud.add_file_to_note(session, note, file)
    return FileInfo(id=file_obj.id, filename=file_obj.filename, path=file_obj.path)

@app.delete("/files/{file_id}")
async def remove_file(file_id: str, note_id: int = Query(...), current_user: models.User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    note = await crud.get_note_by_id(session, note_id, current_user.id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    file = next((f for f in note.files if f.id == file_id), None)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    await crud.delete_file(session, file)
    return {"message": "File deleted"}

@app.get("/files/{filename}")
async def serve_file(filename: str):
    try:
        return RedirectResponse(url=storage.get_file_url(filename))
    except Exception as e:
        raise HTTPException(status_code=404, detail="File not found")

defaut_static = os.getenv("FRONTEND_DIR", "./frontend")
app.mount("/", StaticFiles(directory=defaut_static, html=True), name="frontend")