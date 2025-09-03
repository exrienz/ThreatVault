FROM python:3.12-bookworm

COPY ./requirements.txt ./requirements.txt

RUN pip install --no-cache-dir --upgrade -r ./requirements.txt

COPY ./alembic ./alembic
COPY ./alembic.ini ./alembic.ini
COPY ./src ./src
COPY ./public/ ./public
COPY ./entrypoint.sh ./entrypoint.sh
COPY ./CHANGELOG.md ./CHANGELOG.md

RUN chmod +x ./entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
