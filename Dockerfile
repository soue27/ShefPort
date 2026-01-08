FROM python:3.13-slim

# Устанавливаем системные зависимости для psycopg2 и pg_isready
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Копируем зависимости
COPY pyproject.toml uv.lock ./

# Устанавливаем uv
RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir uv

# Синхронизация зависимостей
RUN uv sync --frozen

# Копируем весь проект
COPY . .

# Делаем entrypoint исполняемым
RUN chmod +x entrypoint.sh

# Запуск
CMD ["/bin/bash", "entrypoint.sh"]


