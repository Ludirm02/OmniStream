.PHONY: backend-install backend-dev backend-test install dev test

backend-install install:
	python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

backend-dev dev:
	. .venv/bin/activate && uvicorn app.main:app --reload

backend-test test:
	. .venv/bin/activate && pytest -q
