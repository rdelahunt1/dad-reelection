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

## Facebook Live/Reels videos cannot be embedded

The candidate forum video was embedded with `plugins/video.php` and showed
"Video Unavailable" to every logged-out visitor, even though the video itself
plays fine on Facebook. The post is a Live/Reels video, and the plugin will not
serve those. All four href formats were tested — `/videos/<id>/`, `/watch/?v=`,
`/reel/<id>`, and `video.php?v=` — and every one fails identically, so there is
no embed URL that fixes it. The section now links out to Facebook instead
(2026-09-11). Don't re-add the iframe; if a future video needs embedding, test
the plugin URL logged out first.

This is also why the CSP carries `frame-src 'none'` — restore a specific frame
origin only if something is genuinely framed again.

## Verify the live site logged out, in a real browser

Two traps caught this one. A browser logged into Facebook may render an embed
that is broken for the public, so check in a clean/private session. And the
built-in Browser pane returns blank screenshots while the pane is hidden — the
page isn't rendered — so a headless Playwright script is the reliable way to
screenshot a section.

## Only `public/` is deployed

Netlify publishes only the `public/` directory. Keep project instructions, source
documents, unused photos, and other working files outside it so they do not become
public downloads. Any new live HTML page or asset must go inside `public/`.

## No build step

Plain static HTML/CSS with inline styles, deployed through Netlify. There is
nothing to compile — if a change isn't showing up, it's a deploy/cache issue or
a CSP block, not a stale build. Keep it that way unless Ryan explicitly asks for
a framework or backend.

## Factual accuracy is a hard rule

Names, election dates, phone numbers, addresses, and campaign finance
disclaimers are legally and politically load-bearing on a real campaign site.
Never infer or invent one — if a fact isn't already in the repo, ask Ryan.
