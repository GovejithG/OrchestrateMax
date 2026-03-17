# OrchestrateMax

A 3-agent AI coding pipeline. Give it a task, and the Planner, Executor, and Reviewer agents work sequentially to write, run, and review code.

## Architecture

- **Planner** — reads your request and produces a structured implementation plan
- **Executor** — writes the code, runs it, fixes errors, iterates
- **Reviewer** — reviews the output and gives a score and verdict

## Stack

- **Backend**: FastAPI, SQLAlchemy (async), SQLite, Ollama
- **Frontend**: React, Vite, Tailwind CSS, Zustand, React Router
- **Agents**: Custom multi-agent orchestrator with SSE streaming

## Quick Start (Local)

1. Install Ollama and pull a model:
```
   ollama pull qwen2.5-coder:7b
```

2. Set up the backend:
```
   python -m venv venv
   venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   cp .env.example .env   # edit OLLAMA_MODEL if needed
   uvicorn app.main:app --reload
```

3. Set up the frontend:
```
   cd ui
   npm install
   npm run dev
```

4. Open `http://localhost:5173`

## Quick Start (Docker)
```
cp .env.example .env
docker-compose up --build
```

Open `http://localhost:80`

## Running Tests
```
pytest
```

## Environment Variables

See `.env.example` for all available configuration options.

## API Docs

Available at `http://localhost:8000/docs` when the backend is running.
