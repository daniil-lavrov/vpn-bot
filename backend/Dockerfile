# Базовый образ Python
FROM python:3.11-slim

# Установим рабочую директорию
WORKDIR /app

# Скопируем все файлы в контейнер
COPY . /app

# Установим зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Команда для запуска FastAPI. Предполагаем, что используем Uvicorn.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]