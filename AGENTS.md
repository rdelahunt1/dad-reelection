# AGENTS.md - dad-reelection

This is a standalone static campaign website for David J. De La Hunt, Hubbard County Commissioner, District 1.

## Project Shape

- Plain static HTML/CSS.
- No build step.
- Main page: `index.html`.
- Thank-you page for Netlify forms: `thank-you.html`.
- Deployment: Netlify, publishing the repo root via `netlify.toml`.
- Main image asset: `Headshot.jpg`.

## Working Rules

- Do not mix files or commits from Ryan's other projects into this repo.
- Run `git status --short` before editing.
- Pull before meaningful work when network access is available, but do not push unless Ryan explicitly asks.
- Keep changes small and easy to understand.
- Explain changes in plain language; Ryan is comfortable learning but is not a professional developer.
- For non-trivial changes, briefly state the plan before editing.

## Agent Usage Disclosure

Before using helper/sub-agents, tell Ryan plainly:

- Whether the work will use only the main agent or multiple agents.
- How many helper agents will be used.
- What each helper agent will do.
- What model each agent will use, if the tool or environment exposes that information.
- Why multiple agents are worth the extra token cost.

Default to the main agent only for this repo. Use helper agents only when they would clearly save time or improve quality, such as parallel review of a large redesign, accessibility review plus copy review, or independent QA. If model details are not visible, say that directly instead of guessing.

## Token Efficiency

- This repo is small. Start by reading `README.md`, `netlify.toml`, and the relevant section of `index.html`.
- Use `rg` to find sections, forms, metadata, copy, or CSS before reading whole files.
- Do not paste or summarize the full HTML unless needed.
- Avoid unnecessary rewrites of the full page.
- Prefer targeted edits to existing inline CSS/HTML.

## Site Notes

- Netlify forms are used for yard sign and volunteer submissions.
- `thank-you.html` is intentionally `noindex`.
- `robots.txt` allows the main site and disallows the thank-you page.
- Security headers live in `netlify.toml`; update the Content Security Policy if adding external assets, scripts, fonts, analytics, or embeds.
- Keep the site static unless Ryan explicitly asks for a framework or backend.

## Campaign Content

Be careful with names, election dates, phone numbers, addresses, and campaign finance disclaimers. Do not invent factual claims. If adding public-record or election information, verify it from a reliable current source.
