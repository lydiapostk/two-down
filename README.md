# Collaborative Crossword

An offline-first, collaborative crossword web app that lets friends solve puzzles together, whether they're online at the same time or not.

## Goals

- Play crossword puzzles collaboratively from a browser or iPhone PWA.
- Preserve each player's answers independently, including edits to the same cell.
- See other players' answers, reactions, and activity in real time.
- Continue solving offline and synchronize changes when reconnected.
- Support private rooms and invitations.

## Tech Stack

| Component | Technology |
|---|---|
| Frontend | Svelte, TypeScript, Vite |
| PWA hosting | Cloudflare Pages |
| Backend API | Python, FastAPI |
| API hosting | Google Cloud Run |
| Database | Supabase PostgreSQL |
| Authentication | Supabase Auth |
| Realtime | Supabase Realtime |
| Offline storage | IndexedDB + Dexie |

## Architecture

The Svelte frontend communicates directly with Supabase for authentication, persistent data, and realtime events.

A separate Python API handles puzzle retrieval and processing.

Puzzle data, player edits, and pending operations are stored locally using IndexedDB. Offline changes are synchronized with Supabase when connectivity returns.

See [ADR 0001 — Initial Architecture](docs/decisions/0001-initial-architecture.md) for architectural decisions and trade-offs.

## Project Structure

```text
frontend/    Svelte application
backend/     Python API
supabase/    Database migrations and configuration
docs/        Architecture and technical decisions
```

## Development

> Project setup is in progress. Development instructions will be added as the frontend and backend are initialized.

## Status

Early development — establishing the project skeleton and infrastructure.

## Scope

This is a personal project intended for private collaborative play, not a public puzzle publishing platform.
