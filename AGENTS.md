# Agent Rules

You are working in a production repository.

Branching Strategy:
- `main` = stable, production-ready code.
- `feature/...` = new features and enhancements.
- `fix/...` = bug fixes.
- `chore/...` = maintenance and dependency updates.
- `docs/...` = documentation updates.
- Protect `main`: All changes must go through pull requests, pass quality gates, and never force push.

Before editing:
1. Read README.md, architecture docs, and existing patterns.
2. Never rewrite large areas without explaining why.
3. Prefer small PR-sized changes targeting `feature/...` or `fix/...` branches.
4. Run required unit tests and integration tests before submitting PRs.
5. Do not touch secrets, .env, credentials, or production data.
6. Do not invent APIs. Check existing code first.
7. Update docs when behavior changes.

Quality Gates (CI Enforcement):
- Backend: `ruff` (formatting/linting), `pytest` (unit & integration tests), coverage check.
- Frontend: `npm run build` (Next.js build check & type safety).
- Docker: `docker compose config` and `docker build` container checks.
- AI agents are NOT allowed to merge code unless all quality gate checks pass cleanly.

Coding style:
- Keep functions small and focused.
- Add targeted unit and integration tests for bug fixes and new features.
- Use clear, self-documenting names.
- Avoid overengineering.

Git rules:
- Work strictly on feature or fix branches (`feature/x`, `fix/x`).
- Never push directly to `main`.
- Every change must pass CI workflows and quality gates before merge.
