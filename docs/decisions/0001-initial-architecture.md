# ADR 0001: Initial architecture for collaborative crossword

- **Status:** Accepted for initial implementation
- **Date:** 2026-11-07
- **Scope:** Solo-developed, iPhone-friendly collaborative crossword PWA

## Context

Build a crossword application that supports room membership, individual player answers, live collaboration, and offline play. Reuse the existing Python-based puzzle retrieval integration. Prefer inexpensive managed infrastructure and avoid an always-on laptop, Kubernetes, self-hosted WebSocket infrastructure, and unnecessary operational complexity.

**Important data-model rule:** Each player's crossword entries are independent, even when multiple players enter different letters in the same cell. These are not conflicting writes to one shared cell. Preserve edits with author and timestamp metadata. A potential reconciliation case is *the same user editing from multiple devices*, especially when one device was offline.

## Decisions

| Concern | Decision | Rationale |
|---|---|---|
| Frontend | Svelte + TypeScript + Vite | Lightweight SPA/PWA; avoid Next.js/SvelteKit for this project |
| Frontend hosting | Cloudflare Pages | Host built static assets without a persistent server |
| Python API | FastAPI deployed to Google Cloud Run | Retain conventional Python application and existing puzzle retrieval library; container flexibility and scale-to-zero |
| Database | Supabase managed PostgreSQL | Durable room, membership, puzzle, edit, and reaction data |
| Authentication | Supabase Auth | Managed sign-in and identity |
| Live collaboration | Supabase Realtime Broadcast and Presence | Room-scoped events and ephemeral online/active-cell/typing state without self-hosting Socket.IO |
| Browser offline database | IndexedDB through Dexie | Store cached puzzles, per-player progress, reactions, and pending operations locally |
| Offline app shell | PWA service worker and Cache Storage | Cache app assets separately from structured application data |
| Synchronization | Initially implement a small custom sync layer | Learn offline-first synchronization while keeping the app-specific protocol simple; revisit PowerSync if complexity grows |
| Schema management | Supabase CLI migrations committed to Git | Version-control database changes |
| Repository | Monorepo | Keep frontend, backend, schema, and architecture decisions together |

## Runtime responsibilities

- **Cloudflare Pages:** serves the Svelte frontend.
- **Browser / IndexedDB:** stores locally cached puzzles and state; queues edits and reactions when offline.
- **Supabase PostgreSQL:** authoritative durable record of edits, reactions, room memberships, and other shared state.
- **Supabase Realtime:** Broadcast provides immediate event notifications; Presence provides ephemeral online status, selected cell, and typing indicators. Realtime is not the durable source of truth.
- **Google Cloud Run:** runs the stateless Python API that retrieves/processes crossword puzzles. It does not need to host the collaboration WebSocket layer.

## Initial synchronization approach

1. Record each local edit/reaction in IndexedDB with a stable unique operation ID, author, device identifier, and creation metadata.
2. Upload pending operations to Supabase when connectivity permits. Make writes idempotent so retries do not duplicate operations.
3. Mark an operation synchronized only after the server confirms persistence.
4. On app startup or reconnection, refresh the room's durable state from PostgreSQL; a full-state refresh is acceptable for the initial small-scale version.
5. While connected, use Supabase Realtime to update the UI promptly. Do not assume missed Realtime events are replayed after disconnect.
6. Preserve distinct players' edits independently. For the same user editing from multiple devices, preserve the edit history and define display/reconciliation policy separately.
7. Resume syncing when the app returns to the foreground; do not rely on iOS running background JavaScript continuously.

## Security and operational notes

- Enable and test Row Level Security for room membership, puzzle access, edits, and reactions.
- Configure authorization for private Realtime channels; room IDs alone are not access control.
- Use Supabase's browser-safe publishable key in the frontend. Keep privileged keys and third-party credentials on the server only.
- Configure CORS for calls from the Cloudflare Pages frontend to the Cloud Run API.
- Use a Supabase **development** project initially; create separate production infrastructure when needed.
- Cloud Run can scale to zero, but actual costs depend on usage, configuration, networking, and provider pricing. Confirm current limits before deployment.
- Browser storage, especially on mobile, can be evicted; treat unsynced local data carefully and surface sync status.

## Alternatives considered

- **Vercel Python Functions:** potentially simpler deployment; not selected initially because Cloud Run better preserves a conventional containerized FastAPI service and accommodates arbitrary dependencies.
- **Render:** conventional Python hosting; not selected as the initial default.
- **Cloudflare Workers for Python:** would introduce runtime and library-compatibility considerations for the existing Python integration.
- **Self-hosted Socket.IO + Redis:** unnecessary when Supabase Realtime provides Broadcast and Presence.
- **PowerSync:** viable managed/offline-first synchronization alternative; deferred to keep the initial stack small and learn the synchronization mechanics.
- **CRDTs / Operational Transformation:** unnecessary for the independent-per-player edit model.
- **Caddy / Kubernetes / Traefik:** unnecessary for the initial deployment. Use Vite's development proxy locally if needed.

## Proposed repository layout

```text
crossword/
├── README.md
├── docs/
│   ├── architecture.md
│   └── decisions/
│       └── 0001-initial-architecture.md
├── frontend/              # Svelte + Vite + Dexie + Supabase client
├── backend/               # FastAPI / Python puzzle retrieval
└── supabase/              # SQL migrations and local configuration
```

## Open decisions / follow-ups

- Confirm compatibility of the existing Python puzzle retrieval dependency with Cloud Run and its upstream authentication requirements.
- Choose Supabase Auth providers and design invitation/membership flows.
- Define the SQL schema, RLS policies, and whether edits are stored as append-only operations plus a materialized current state.
- Decide how puzzle data is cached and whether it is persisted in Supabase or retrieved through the Python API on demand.
- Define same-user multi-device display/reconciliation semantics.
- Choose the exact PWA/service-worker integration and test iOS offline behavior.
- Set up deployment pipelines, environment variables, and separate production projects when ready.

## Decision review trigger

Revisit this ADR if the Python runtime proves incompatible with Cloud Run, sync implementation becomes disproportionately complex, or operating costs exceed the project's intended budget. If superseded, add a new ADR instead of rewriting the historical rationale.
