FROM python:3.13-slim

WORKDIR /app

# системные зависимости
RUN apt update && apt install -y curl build-essential

# uv
RUN pip install uv

# зависимости
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

# код проекта
COPY . .

CMD ["uv", "run", "python", "main.py"]

