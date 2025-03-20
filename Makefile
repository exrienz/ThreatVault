dev_db:
	docker run --name sentinel-db -p 5432:5432 -e POSTGRES_USER=root -e POSTGRES_PASS=secret -d postgres:17.0-alpine3.20

dev:
	fastapi dev ./src/main.py

phony: dev_db dev
