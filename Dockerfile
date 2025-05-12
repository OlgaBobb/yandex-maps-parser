FROM python:3.9-slim

# Установка Chrome и зависимостей
RUN apt-get update && apt-get install -y \
    google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Установка Python-зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование приложения
COPY app.py .

# Запуск Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501"]
