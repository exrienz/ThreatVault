FROM python:3.12-bookworm

COPY ./requirements.txt ./requirements.txt

RUN pip install --no-cache-dir --upgrade -r ./requirements.txt

COPY ./alembic ./alembic
COPY ./alembic.ini ./alembic.ini
COPY ./src ./src
COPY ./public/ ./public

# CMD ["fastapi", "dev", "src/main.py", "--port", "8080"]
# CMD ["uvicorn", "src.main:app", "--port", "8000", "--reload"]
CMD ["alembic", "upgrade", "head"]
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
