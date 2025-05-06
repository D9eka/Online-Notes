import uuid
import os

from fastapi import HTTPException
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from datetime import datetime
from models import User, Note, File
from sqlalchemy.orm import selectinload
from storage import storage

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")

async def create_user(session: AsyncSession, username: str, password: str):
    hashed = pwd_context.hash(password)
    user = User(username=username, hashed_password=hashed)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

async def get_user_by_username(session: AsyncSession, username: str):
    result = await session.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()

async def get_notes_for_user(session: AsyncSession, user_id: int):
    result = await session.execute(
        select(Note)
        .where(Note.user_id == user_id)
        .options(selectinload(Note.files))
        .order_by(Note.created_at.desc())
    )
    return result.scalars().all()

async def create_note(session: AsyncSession, user_id: int, title: str, content: str):
    note = Note(user_id=user_id, title=title, content=content)
    session.add(note)
    await session.commit()
    await session.refresh(note)

    result = await session.execute(
        select(Note).options(selectinload(Note.files)).where(Note.id == note.id)
    )
    note_with_files = result.scalars().first()
    return note_with_files

async def get_note_by_id(session: AsyncSession, note_id: int, user_id: int):
    result = await session.execute(
        select(Note)
        .options(selectinload(Note.files))
        .where(Note.id == note_id, Note.user_id == user_id)
    )
    return result.scalars().first()

async def update_note(session: AsyncSession, note: Note, title: str, content: str):
    note.title = title
    note.content = content
    note.updated_at = datetime.utcnow()
    await session.commit()
    await session.refresh(note)
    return note

async def delete_note(session: AsyncSession, note: Note):
    await session.delete(note)
    await session.commit()
    return


async def add_file_to_note(session: AsyncSession, note: Note, upload_file) -> File:
    file_id = str(uuid.uuid4())

    try:
        file_contents = await upload_file.read()
        file_extension = os.path.splitext(upload_file.filename)[1]
        object_name = await storage.upload_file(file_contents, file_extension)
    except HTTPException as e:
        raise e

    file = File(
        id=file_id,
        filename=upload_file.filename,
        path=object_name,
        note=note
    )
    session.add(file)
    await session.commit()
    await session.refresh(file)
    return file


async def delete_file(session: AsyncSession, file: File):
    try:
        await storage.delete_file(file.path)
    except HTTPException as e:
        raise e

    await session.delete(file)
    await session.commit()
    return