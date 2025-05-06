# Базовый образ Python
FROM python:3.9-slim

# Рабочая директория
WORKDIR /backend

# Копируем зависимости и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Открываем порт 80 (HTTP)
EXPOSE 80

# Запускаем приложение
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]