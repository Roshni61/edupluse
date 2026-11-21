.PHONY: help setup dev-db migrate seed test test-e2e run-backend run-frontend

help:
	@echo EduPulse Monorepo Commands:
	@echo   make setup        - Install backend and frontend dependencies
	@echo   make dev-db       - Start PostgreSQL database container via docker compose
	@echo   make migrate      - Apply database schema and migrations
	@echo   make seed         - Seed mock students, missions, badges and users
	@echo   make test         - Run pytest backend test suite
	@echo   make test-e2e     - Run Playwright end-to-end test suite
	@echo   make run-backend  - Start FastAPI development server (http://localhost:8000)
	@echo   make run-frontend - Start Vite frontend development server (http://localhost:5173)

setup:
	@echo Setting up EduPulse monorepo...
	@python -c "import shutil, os; shutil.copyfile('.env.example', '.env') if not os.path.exists('.env') else None"
	@python -m pip install -r backend/requirements.txt
	@npm --prefix frontend install

dev-db:
	@echo Starting development PostgreSQL database container...
	@python -c "import subprocess; rc = subprocess.run(['docker', 'compose', 'up', '-d', 'db'], shell=True).returncode if subprocess.run(['docker', 'version'], capture_output=True, shell=True).returncode == 0 else print('Notice: Docker is not active. Using local dev database.'); exit(0)"

migrate:
	@echo Applying database schema...
	@python -c "import sys; sys.path.insert(0, 'backend'); from app.db.session import engine, Base; Base.metadata.create_all(bind=engine); print('Database schema up to date.')"

seed:
	@echo Seeding initial sample data...
	@python -c "import sys; sys.path.insert(0, 'backend'); from app.db.seed import seed_database; seed_database()"

test:
	@echo Running backend test suite with pytest...
	@python -m pytest backend/tests -v

test-e2e:
	@echo Running Playwright end-to-end test suite...
	@npx playwright test

run-backend:
	@echo Starting EduPulse FastAPI backend server...
	@python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000 --reload

run-frontend:
	@echo Starting EduPulse frontend development server...
	@npm --prefix frontend run dev
