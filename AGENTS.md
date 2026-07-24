# Agent Rules

You are working in a production repository.

Before editing:
1. Read README.md, architecture docs, and existing patterns.
2. Never rewrite large areas without explaining why.
3. Prefer small PR-sized changes.
4. Run required unit tests and integration tests after changes to verify functionality.
5. Do not touch secrets, .env, credentials, or production data.
6. Do not invent APIs. Check existing code first.
7. Update docs when behavior changes.

Testing requirements:
- Always run required unit tests for individual functions, services, and utilities.
- Always run integration tests for FastAPI API endpoints (`/api/ask`, `/api/upload`, `/api/docs`, `/api/doc/{id}`) and ChromaDB vector retrieval pipeline.
- Verify both success and edge-case behavior before claiming completion.

Coding style:
- Keep functions small and focused.
- Add targeted unit and integration tests for bug fixes and new features.
- Use clear, self-documenting names.
- Avoid overengineering.

Git rules:
- Work on feature branches.
- Never push directly to main.
- Every change must pass CI and test suites.
