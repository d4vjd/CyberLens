<![CDATA[# Contributing to CyberLens

Thank you for considering contributing to CyberLens! This document outlines the development workflow, coding standards, and pull request process.

---

## Getting Started

1. Fork the repository and clone your fork.
2. Copy `.env.example` to `.env` if you need to override defaults.
3. Start the dev stack with hot reload:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

4. Verify the backend is healthy at `http://localhost:8000/api/v1/health` and the frontend is running at `http://localhost:5173`.

---

## Development Flow

1. Create a feature branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Make focused, incremental changes that align with one logical unit of work.
3. Run linting and tests before committing:
   ```bash
   make lint
   make test
   ```
4. Commit with a clear, descriptive message (see [Commit Conventions](#commit-conventions) below).
5. Push your branch and open a Pull Request against `main`.

---

## Commit Conventions

Use concise, imperative-mood commit messages. Prefix with a scope when practical:

```
feat(detection): add aggregation rule evaluator
fix(ingestion): handle malformed syslog timestamps
docs(readme): add project structure tree
refactor(incidents): extract playbook runner into service
test(mitre): add coverage for technique lookup
chore(ci): pin CodeQL action to v3
```

---

## Coding Standards

### Backend (Python)

- **Python 3.12** with type hints on all public functions, classes, and methods.
- **FastAPI** for routing, **SQLAlchemy 2.0 async** for persistence, **Pydantic** for request/response models.
- **Linting**: Ruff (check + format), mypy (strict mode), Bandit (security scan).
- **Logging**: Use the shared `structlog` setup — no bare `print()` calls.
- **Tests**: pytest with `pytest-asyncio`. Place tests under `backend/tests/` mirroring the source layout.
- **Docstrings**: Short, professional docstrings stating inputs, outputs, and side effects.

### Frontend (TypeScript / React)

- **React 18** with functional components and hooks.
- **TypeScript** with strict mode — avoid `any` types.
- **State management**: Zustand for global state, TanStack Query for server state.
- **Routing**: React Router with feature-based module organisation under `frontend/src/features/`.
- **Styling**: Vanilla CSS with the project's design token system — avoid inline styles.

### General

- Keep detection rules in `rules/` and IR playbooks in `playbooks/` as YAML files.
- Do not hard-code values that belong in configuration — add them to `.env.example` and the Pydantic settings model.
- Avoid bare `except:` blocks; catch specific exceptions and log meaningful context.

---

## Pull Request Guidelines

- Keep PRs focused. One feature, one fix, or one refactor per PR.
- Ensure CI passes (lint, tests, build, CodeQL) before requesting review.
- Include a brief description of **what** changed and **why**.
- Link to any related issues if applicable.
- Update documentation (`docs/`, README, CHANGELOG) if your change affects public behavior or setup steps.

---

## Project Layout

| Directory | Purpose |
|---|---|
| `backend/src/cyberlens/` | FastAPI application source |
| `backend/tests/` | Backend test suite |
| `frontend/src/` | React application source |
| `rules/` | YAML detection rules |
| `playbooks/` | YAML incident response playbooks |
| `docs/` | Extended documentation |
| `.github/workflows/` | CI and CodeQL workflows |

---

## Questions?

If you're unsure about an approach or want to discuss a change before implementing it, feel free to open an issue.
]]>
