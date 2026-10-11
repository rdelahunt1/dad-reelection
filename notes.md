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

On 2026-10-09, the October tax-base release was published and verified live.
Netlify rewrote its homepage link from `press-release-tax-base.html` to
`/press-release-tax-base`. Live browser checks must accept the clean URL;
an exact `.html` selector can falsely report that the deployment is missing.

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

## Weekly traffic report (analytics/)

- The Netlify dashboard shows only 7 days on the free plan, but the data feed
  it calls (`/access-control/analytics-api/v2/<site-id>/...`, cookie-authenticated)
  returns about 40 days. `analytics/fetch_netlify.js` runs inside a signed-in
  browser pane; if the Netlify login expires, the routine alerts Ryan
  instead of emailing David.
- The PDF (~140 KB, embedded fonts) is too large to attach through the Gmail
  connector, because the base64 would have to be copied through the model's context.
  It is sent through Apple Mail (`send_report.applescript`, Ryan's Gmail account)
  instead. A scripted Mail message wraps its body in a quote-style block.
  Putting the attachment `after the last character of content` with a
  visible window removed the `>` quoting from the plain-text version.
- `build_report.py stats` fails with DATA CHECK FAILED when the daily or page
  totals don't add up to the week total. That catches copying errors in the
  saved JSON.
