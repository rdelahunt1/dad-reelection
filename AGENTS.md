# Dad Reelection

Static campaign site for David J. De La Hunt, Hubbard County Commissioner,
District 1.

## Project boundaries

- The live site is plain HTML/CSS in `public/`; Netlify publishes that directory
  through `netlify.toml`. Keep source documents and unused assets outside it.
- Read `notes.md` before adding an external asset, script, font, analytics, or
  embed. Security headers live in `netlify.toml`, and the CSP must allow every
  intentional external request.
- Keep the site static unless Ryan requests a framework or backend.
- Treat names, election dates, contact information, campaign-finance disclaimers,
  and public-record claims as facts requiring current reliable sources.
- This is a live campaign site, so verify every public-facing change locally before
  it ships: render `public/index.html` and check the section you touched. Ryan has
  given standing approval to push to `main`, which deploys to Netlify — push without
  asking first, then report what changed and what you verified. That approval covers
  shipping; it does not cover inventing facts, which the rule above still governs.

## Workflow

1. Check git status and pull only when the tree is clean.
2. Keep changes small and preserve unrelated work.
3. For visual or content work, verify the rendered `public/index.html`; there is no
   build step.
4. Report what changed and what was visually checked.
