from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List

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


# Модели данных
class User(BaseModel):
    username: str
    password: str


class UserResponse(User):
    id: int


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
    found_user = next((u for u in fake_db if u["username"] == user.username and u["password"] == user.password), None)
    if not found_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"message": "Login successful"}


# Получение всех пользователей
@app.get("/users", response_model=List[UserResponse])
async def get_users():
    return fake_db


# Отдаем статические файлы фронтенда
app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")