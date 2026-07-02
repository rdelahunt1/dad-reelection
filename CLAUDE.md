# CLAUDE.md — dad-reelection

This repo is a standalone project: a campaign website for Ryan's dad's reelection campaign. It is its own git repo, separate from Ryan's other projects (Home Assistant automations, PCS move tracker) — don't mix files or commits between them.

## About Ryan

Active-duty USAF, not a professional developer. Favor plain-language explanations over dev jargon — he's new to working with Claude Code and git, so don't assume familiarity with CLI concepts unless he's demonstrated it. Clear and a little explanatory is better than terse, but don't over-explain things he's already shown he understands.

## Project goal

Build a campaign website for his dad's reelection, intended to eventually be hosted live on the internet (hosting platform not yet chosen — likely a static-site host like GitHub Pages, Netlify, or Vercel given the simplicity of the content).

## Git workflow

- GitHub remote: https://github.com/rdelahunt1/dad-reelection
- **Auto-pull at the start of a session**: run `git pull` first so we're always working from the latest version. Safe — won't overwrite uncommitted local changes.
- **Never push automatically.** Only commit + push when explicitly told to.
- **Remind Ryan to push periodically** — after meaningful chunks of work, or before wrapping up a session, ask if he wants to commit and push so changes don't sit unsynced.
- **Plan before non-trivial changes.** For anything beyond a small fix, lay out the plan and get a quick confirm before executing.

## Structure

(To be filled in as the site takes shape — e.g. static HTML/CSS, or a framework, once that choice is made.)
