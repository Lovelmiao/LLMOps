# AGENTS.md — search_RAG_system

## Repository structure

This is a **Corrective RAG (CRAG)** Q&A system for academic papers, divided into two independent directories:

- `day_3/` — Python Flask backend (CRAG engine + REST API)
- `day_4_UI/LLMOps-ui/` — Vue 3 + TypeScript frontend (Vite 8 + Arco Design)

## Backend (`day_3/`)

### Entrypoint

```sh
cd day_3
PYTHONPATH=. python app/app.py
```

Uses **Injector** DI. Wiring is in `app/module.py` → `ExtensionModule`.

### Architecture

`Handler` → `Service` → `Model`, all injected via `@inject @dataclass`. Routes registered in `internal/router/router.py` as a single Flask Blueprint.

### Key files

| File | Purpose |
|------|---------|
| `app/app.py` | Flask app bootstrap, Injector creation |
| `internal/router/router.py` | All route definitions |
| `internal/handler/app_handler.py` | **CRAG LangGraph pipeline** (load_history → retrieve → grade → web_search/generate → save_message) |
| `internal/handler/session_handler.py` | Session CRUD, document upload/delete, settings (JSON-file-backed) |
| `internal/handler/auth_handler.py` | Register/login/logout via Flask Session Cookie |
| `internal/service/app_service.py` | MessageService + AuthService + AppService — all DB operations |
| `internal/model/app.py` | 5 SQLAlchemy models: App, User, ChatSession, ChatMessage, ChatSummary |

### Database

PostgreSQL via `SQLALCHEMY_DATABASE_URI` in `.env`. Tables auto-created on startup (`db.create_all()`). Schema defined in `internal/model/app.py`.

### Session assets (JSON-file-backed)

State stored at `instance/session_assets/{session_id}/`:
- `documents.json` — uploaded file metadata + vector_ids
- `settings.json` — per-session model settings
- `uploads/` — uploaded PDFs

### Environment

`.env` contains **live API keys** (OpenAI, Pinecone, NVIDIA, Serper, LangSmith). `.ignore` excludes `.env` and `storage/`. **Never commit** these.

Required services: PostgreSQL, Pinecone index ("llmops").

### Dependencies

Install with `pip install -r requirements.txt`. Key packages: Flask 3, Flask-SQLAlchemy, injector, langchain-community, langchain-nvidia-ai-endpoints, langchain-pinecone, langgraph, pymupdf, pinecone, openai.

## Frontend (`day_4_UI/LLMOps-ui/`)

### Commands (use **yarn**, not npm)

| Command | Purpose |
|---------|---------|
| `yarn` | Install dependencies |
| `yarn dev` | Dev server on `localhost:5173` (proxies `/api` → `localhost:5000`) |
| `yarn build` | Type-check + build |
| `yarn test:unit` | Vitest unit tests |
| `yarn lint` | ESLint + oxlint with `--fix` |
| `yarn format` | Prettier write |

### Vite proxy

`/api` → `http://localhost:5000` with `/api` prefix stripped. Backend Flask routes do NOT include `/api`.

### Key frontend structure

| Path | Purpose |
|------|---------|
| `src/config/index.ts` | `apiPrefix = '/api'`, HTTP code constants |
| `src/utils/request.ts` | Fetch wrapper (180s timeout, auto Cookie, error toast via Arco `Message`) |
| `src/utils/auth.ts` | `isLogin()` check |
| `src/services/` | API call functions per domain (app.ts, auth.ts, session.ts) |
| `src/stores/acount.ts` | Pinia store for account state |
| `src/router/index.ts` | Routes with auth guard (`beforeEach`) |
| `src/views/space/apps/DetailView.vue` | Main chat view |
| `src/views/home/HomeView.vue` | Landing page |

### Lint / format config

- ESLint (`.eslintrc` not checked but plugins: vue, typescript, oxlint)
- oxlint (run as part of lint)
- Prettier: `semi: false, singleQuote: true, tabWidth: 2, trailingComma: "all"`

## API conventions

- Base without `/api` prefix on backend. Frontend adds `/api` proxy prefix.
- Auth: Flask Session Cookie (browser auto-sends)
- Response format: `{ "code": "success"|"fail"|"validateError"|"unauthorized"|"forbidden", "message": "...", "data": {...} }`
- Legacy routes under `/message/` and `/app/` exist alongside new `/sessions/` routes.
