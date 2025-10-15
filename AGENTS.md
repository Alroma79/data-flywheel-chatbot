# Repository Guidelines

## Project Structure & Module Organization
- Source code lives under `src/` or `app/` with modules grouped by feature (e.g., `src/chat/`, `src/data/`).
- Tests are in `tests/` mirroring the package layout (e.g., `tests/chat/test_handlers.py`).
- Config files live in `configs/` and environment variables in `.env` (provide `.env.example`).
- Scripts and one-off utilities go in `scripts/`; static assets in `assets/`.

## Build, Test, and Development Commands
- Install: prefer a single bootstrap command.
  - Python: `uv pip install -r requirements.txt` or `pip install -e .[dev]`.
  - Node: `npm ci` or `pnpm i --frozen-lockfile` if a `package.json` exists.
- Run app locally:
  - Python API: `uv run fastapi dev` or `uvicorn app.main:app --reload`.
  - Node app: `npm run dev`.
- Test: `pytest -q` (Python) or `npm test` (Node). Add `-k`/`--watch` as needed.
- Lint/format: `ruff check . && ruff format .` (Python) or `npm run lint && npm run format` (Node).

## Coding Style & Naming Conventions
- Python: 4-space indent, `snake_case` for functions/vars, `PascalCase` for classes.
- Type hints required for public functions; docstrings follow NumPy or Google style.
- JS/TS: 2-space indent, `camelCase` for functions/vars, `PascalCase` for components/types.
- Keep modules small; one responsibility per file. Prefer pure functions over side effects.

## Testing Guidelines
- Frameworks: `pytest` (Python) and/or `jest`/`vitest` (JS/TS).
- Name tests `test_*.py` (Python) or `*.test.ts(x)`/`*.spec.ts(x)` (JS/TS).
- Aim for ≥80% line coverage on changed code. Put fixtures under `tests/fixtures/`.
- Use fast, deterministic tests. Avoid network/file I/O unless mocked.

## Commit & Pull Request Guidelines
- Use Conventional Commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`.
- Keep subject ≤72 chars; body explains what/why and relevant context.
- PRs include: clear description, linked issue (e.g., `Closes #123`), screenshots for UI, and test evidence (commands/output).
- Small, focused PRs are preferred. Update docs when behavior changes.

## Security & Configuration Tips
- Never commit secrets. Use `.env` with an accompanying `.env.example`.
- Validate and sanitize all inputs; log only non-sensitive metadata.
- Pin dependencies and update regularly; run `pip-audit`/`npm audit` in CI if applicable.
