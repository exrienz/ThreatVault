# -- Stage 1
FROM node:20-bookworm AS js-bundler

COPY package.json package-lock.json* ./

RUN npm install

COPY ./vite.config.js ./vite.config.js
COPY ./public ./public
COPY ./assets ./assets

RUN npm run build

# -- Stage 2
FROM python:3.12-bookworm

COPY ./requirements.txt ./requirements.txt

RUN pip install --no-cache-dir --upgrade -r ./requirements.txt

COPY ./plugins ./plugins
COPY ./alembic ./alembic
COPY ./alembic.ini ./alembic.ini
COPY ./src ./src
COPY ./entrypoint.sh ./entrypoint.sh
COPY ./CHANGELOG.md ./CHANGELOG.md

COPY --from=js-bundler ./static ./static

RUN chmod +x ./entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
