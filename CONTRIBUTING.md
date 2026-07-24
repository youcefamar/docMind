# Contributing to DocMind 🤝

Thank you for contributing to **DocMind — Internal Knowledge Assistant**!

---

## 🌿 Professional Branching Strategy

We follow a clean, production-grade branching model:

| Branch | Purpose | Protection Rules |
|---|---|---|
| `main` | Stable, production-ready release code | Protected. PR required, status checks must pass, no force push. |
| `feature/...` | New features & enhancements (`feature/category-filter`) | Development topic branch. |
| `fix/...` | Bug fixes (`fix/upload-timeout`) | Bugfix topic branch. |
| `chore/...` | Maintenance, dependencies & refactoring | Maintenance topic branch. |
| `docs/...` | Documentation & ADR updates | Docs topic branch. |

---

## 🚦 Automated Quality Gates & CI

All pull requests automatically trigger GitHub Actions quality gate workflows:

1. **Backend Quality Gate (`backend-ci.yml`)**:
   - Code formatting & linting via `ruff check`
   - Unit & integration tests via `pytest`
   - Test coverage enforcement
2. **Frontend Quality Gate (`frontend-ci.yml`)**:
   - Production build validation (`npm run build`)
   - TypeScript static type checking
3. **Docker Quality Gate (`docker-ci.yml`)**:
   - `docker compose config` syntax verification
   - Multi-container `docker build` check

AI agents and contributors are not allowed to merge code unless all quality gate checks pass.

---

## 📦 Dependabot Updates

Automated dependency updates are managed via `.github/dependabot.yml` on a weekly schedule for:
- Python dependencies (`pip` in `/backend`)
- Node.js dependencies (`npm` in `/frontend`)
- GitHub Actions workflows (`/`)

---

## 📥 Submitting a Pull Request (PR)

1. Create a topic branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Run local tests:
   ```bash
   # Backend tests
   cd backend && pytest

   # Frontend build test
   cd frontend && npm run build
   ```
3. Open a Pull Request targeting `main` and complete the template in `.github/pull_request_template.md`:
   - Explain **What changed**, **Why**, **How tested**, and state the **Risk level** (Low / Medium / High).
