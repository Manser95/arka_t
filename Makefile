include .env
export

run:
	poetry run uvicorn schema:app --reload

fmt:
	poetry run ruff check -s --fix --exit-zero .

lint list_strict:
	poetry run mypy .
	poetry run ruff check .

lint_fix: fmt lint

migrate:
	poetry run python -m yoyo apply -vvv --batch --database "postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB_NAME}" ./migrations

create_container:
	docker-compose up --build -d