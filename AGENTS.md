# AGENTS.md - dad-reelection

This is a standalone static campaign website for David J. De La Hunt, Hubbard County Commissioner, District 1.

It sits one level below Ryan's cross-repo workspace root (`/Users/ryan/Coding` on the Mac), which has its own `AGENTS.md`/`CLAUDE.md` covering who Ryan is, how to respond, multi-machine setup, and shared git habits. Read those too - this file only covers what's specific to this repo. Keep `AGENTS.md` and `CLAUDE.md` in sync; mirror any durable edit into both in the same turn.

## Project Shape

- Plain static HTML/CSS.
- No build step.
- Main page: `public/index.html`.
- Deployment: Netlify, publishing only `public/` via `netlify.toml`.
- Gotchas that can break the live site live in `notes.md` - read it before adding
  anything external; put new gotchas there, not in this file.
- Main image asset: `public/Headshot.jpg`.

## Working Rules

- Do not mix files or commits from Ryan's other projects into this repo.
- Run `git status --short` before editing.
- Pull before meaningful work when network access is available, but do not push unless Ryan explicitly asks.
- Keep changes small and easy to understand.
- Explain changes in plain language; Ryan is comfortable learning but is not a professional developer. Keep responses brief and focused - see "How to respond" in the workspace-root doc.
- For non-trivial changes, briefly state the plan before editing.

## Subagents

Default to the main agent only in this repo - it's small enough that delegation
rarely pays. If you do use helpers (parallel review of a large redesign,
accessibility plus copy review, independent QA), say up front how many, what each
will do, and which model each uses.

## Site Notes

- Only files inside `public/` belong on the live site. Keep source documents, unused assets, and project instructions outside it.
- Security headers live in `netlify.toml`. **Adding any external asset, script, font, analytics snippet, or embed requires a matching CSP update or it is silently blocked in the browser** - see [`notes.md`](notes.md).
- Keep the site static unless Ryan explicitly asks for a framework or backend.

## Campaign Content

Be careful with names, election dates, phone numbers, addresses, and campaign finance disclaimers. Do not invent factual claims. If adding public-record or election information, verify it from a reliable current source.
