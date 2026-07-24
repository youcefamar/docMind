# Contributing to DocMind 🤝

Thank you for your interest in contributing to **DocMind — Internal Knowledge Assistant**!

---

## 🚀 Getting Started

1. **Fork & Clone** the repository:
   ```bash
   git clone https://github.com/your-org/docmind.git
   cd docmind
   ```

2. **Branching Strategy**:
   Create a topic branch off `main`:
   ```bash
   git checkout -b feature/amazing-new-feature
   # or
   git checkout -b fix/issue-description
   ```

---

## 🛠️ Development Guidelines

### Frontend (Next.js 15)
- Located in `frontend/`.
- Use TypeScript strictly. Avoid using `any` unless absolutely required.
- Maintain tailwind CSS design token consistency (dark mode glassmorphism theme).
- Format code with Prettier before submitting.

### Backend (FastAPI)
- Located in `backend/`.
- Follow PEP 8 guidelines and type hinting for all function parameters and response models.
- Ensure all API routes are registered under `backend/routes/`.
- Include Pydantic models for request/response validation.

---

## 🧪 Testing

Before submitting a Pull Request, ensure:
1. FastAPI backend starts cleanly:
   ```bash
   cd backend
   pytest # or test via uvicorn main:app
   ```
2. Next.js application builds without errors:
   ```bash
   cd frontend
   npm run build
   ```

---

## 📥 Submitting a Pull Request (PR)

1. Ensure your commit messages are clear (e.g., `feat(rag): add multi-category search support`).
2. Open a Pull Request targeting the `main` branch.
3. Fill out the PR template in full.
4. Request review from maintainers.
