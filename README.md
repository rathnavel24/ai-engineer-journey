# ai-engineer-journey

Daily practice log and project sandbox for learning AI engineering.

## Folder layout

- `days/` — one folder per day (e.g. `day-001/`) with that day's notes/exercises
- `projects/` — standalone projects built along the way
- `notes/` — reference notes, cheatsheets, and writeups
- `scripts/` — helper scripts (e.g. environment checks)
- `src/` — shared Python package code

## How to run

```bash
# install dependencies (including dev tools)
uv sync

# copy env template and fill in your keys
cp .env.example .env

# verify required env vars are set
uv run python scripts/check_env.py

# run tests
uv run pytest

# lint
uv run ruff check .
```
