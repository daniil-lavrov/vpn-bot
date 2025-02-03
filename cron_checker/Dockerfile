# Используем базовый образ Python
FROM python:3.11-slim

# Устанавливаем cron
RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем скрипт в контейнер
COPY . /app

# Устанавливаем зависимости, если они есть, например из requirements.txt
# COPY requirements.txt /app/requirements.txt
# RUN pip install --no-cache-dir -r requirements.txt

# Добавляем задание в cron
# Здесь используем >> чтобы добавить запись в crontab, т.к. команда RUN выполняется
# во время сборки, а не в контейнере
RUN echo "0 9 * * * python /app/checker.py" >> /etc/crontab

# Чтобы cron начал работать, нужно запустить его в фоновом режиме
CMD ["cron", "-f"]