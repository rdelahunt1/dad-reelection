# notes.md — gotchas and lessons learned

Companion to `CLAUDE.md`/`AGENTS.md`, which carry the rules and structure. This
file carries the things that can quietly break the **live** site. **Read it
before adding anything external to the page.**

Put new gotchas here rather than in the main doc, which loads in full every session.

## Content Security Policy will silently kill external assets

Security headers live in `netlify.toml`, including a CSP. Adding an external
script, font, stylesheet, analytics snippet, image host, or embed **will be
blocked at runtime** unless the CSP is updated to allow that origin — and it
fails in the browser, not at deploy time, so a build that "succeeds" can still
ship a broken page.

Update the CSP deliberately and narrowly (name the specific origin, don't widen
to a wildcard) in the same change that adds the asset. Then verify in a browser
console, not just by loading the page.

## Netlify forms

- Yard sign and volunteer submissions go through Netlify forms.
- `thank-you.html` is the form redirect target and is intentionally marked
  `noindex`; `robots.txt` disallows it. Don't "fix" either — that's deliberate.
- Renaming a form field or the form's `name` attribute silently orphans past
  submissions in the Netlify dashboard. Check with Ryan before touching either.

## No build step

Plain static HTML/CSS with inline styles, deployed through Netlify. There is
nothing to compile — if a change isn't showing up, it's a deploy/cache issue or
a CSP block, not a stale build. Keep it that way unless Ryan explicitly asks for
a framework or backend.

## Factual accuracy is a hard rule

Names, election dates, phone numbers, addresses, and campaign finance
disclaimers are legally and politically load-bearing on a real campaign site.
Never infer or invent one — if a fact isn't already in the repo, ask Ryan.
