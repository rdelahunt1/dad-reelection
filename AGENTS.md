# Dad Reelection

Static campaign site for David J. De La Hunt, Hubbard County Commissioner,
District 1. Keep `AGENTS.md` and `CLAUDE.md` identical.

## Project boundaries

- The live site is plain HTML/CSS in `public/`; Netlify publishes that directory
  through `netlify.toml`. Keep source documents and unused assets outside it.
- Read `notes.md` before adding an external asset, script, font, analytics, or
  embed. Security headers live in `netlify.toml`, and the CSP must allow every
  intentional external request.
- Keep the site static unless Ryan requests a framework or backend.
- Treat names, election dates, contact information, campaign-finance disclaimers,
  and public-record claims as facts requiring current reliable sources.
- This is a live campaign site. Prepare and verify public-facing changes, then show
  Ryan before changing or deploying the live site. Do not push without his explicit
  approval.

## Workflow

1. Check git status and pull only when the tree is clean.
2. Keep changes small and preserve unrelated work.
3. For visual or content work, verify the rendered `public/index.html`; there is no
   build step.
4. Use the main agent for ordinary work. Delegate a bounded review or QA task to a
   cheaper agent only when it replaces meaningful lead-agent work.
5. For instruction-only edits, verify the paired files and diff. For site work,
   report what changed and what was visually checked.
