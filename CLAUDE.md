# CLAUDE.md - dad-reelection

This repo is a standalone project: a campaign website for Ryan's dad's reelection campaign. It is its own git repo, separate from Ryan's other projects (Home Assistant automations, PCS move tracker). Do not mix files or commits between them.

## About Ryan

Active-duty USAF, not a professional developer. Favor plain-language explanations over dev jargon. Clear and a little explanatory is better than terse, but do not over-explain things he has already shown he understands.

## Project goal

Maintain and improve the live-ready campaign website for David J. De La Hunt's reelection campaign for Hubbard County Commissioner, District 1.

The site is a plain static HTML/CSS site deployed through Netlify. There is no build step.

## Git workflow

- GitHub remote: https://github.com/rdelahunt1/dad-reelection
- **Auto-pull at the start of a session when network access is available**: run `git pull` so we're working from the latest version. Safe to try, but do not get stuck if network/sandbox permissions block it.
- **Never push automatically.** Only commit + push when explicitly told to.
- **Remind Ryan to push periodically**: after meaningful chunks of work, or before wrapping up a session, ask if he wants to commit and push so changes do not sit unsynced.
- **Plan before non-trivial changes.** For anything beyond a small fix, lay out the plan and get a quick confirm before executing.

## Agent usage disclosure

Before using helper/sub-agents, tell Ryan plainly:

- Whether the work will use only the main agent or multiple agents.
- How many helper agents will be used.
- What each helper agent will do.
- What model each agent will use, if the tool or environment exposes that information.
- Why multiple agents are worth the extra token cost.

Default to the main agent only for this repo. Use helper agents only when they would clearly save time or improve quality, such as parallel review of a large redesign, accessibility review plus copy review, or independent QA. If model details are not visible, say that directly instead of guessing.

## Structure

- `index.html` - full one-page campaign site with inline CSS.
- `thank-you.html` - Netlify form thank-you page; intentionally marked `noindex`.
- `Headshot.jpg` - candidate photo used in the hero.
- `netlify.toml` - Netlify publish config and security headers.
- `robots.txt` - allows the main site and disallows the thank-you page.
- `README.md` - short project summary.

## Site notes

- Netlify forms are used for yard sign and volunteer submissions.
- Security headers live in `netlify.toml`. If adding external assets, scripts, fonts, analytics, or embeds, update the Content Security Policy intentionally.
- Keep the site static unless Ryan explicitly asks for a framework or backend.
- Be careful with names, election dates, phone numbers, addresses, and campaign finance disclaimers. Do not invent factual campaign claims.

## Token efficiency

- Start with `README.md`, `netlify.toml`, and the relevant section of `index.html`.
- Use `rg` to find sections, forms, metadata, copy, or CSS before reading whole files.
- Avoid summarizing or rewriting the full HTML unless the task truly requires it.
- Prefer small, targeted edits that preserve the existing design and structure.
