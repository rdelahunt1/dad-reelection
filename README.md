# Dad's Reelection Campaign Website

Campaign site for David J. De La Hunt, Hubbard County Commissioner, District 1.

`public/index.html` is the campaign homepage; individual press releases are separate HTML pages in `public/`, linked from the homepage. There is no build step. Netlify deploys only the `public/` directory from this repo's `main` branch.

## Weekly traffic report

`analytics/` builds a weekly traffic PDF from Netlify Web Analytics and is not
deployed. A Claude scheduled task (`weekly-campaign-site-traffic-report`, Sundays
5 PM Central) runs it and emails the report to David through Gmail SMTP
(`analytics/send_report.py`); first set up 2026-10-11. All dates and weeks are
Central time.

Status: the first report (Oct 4–10) was sent 2026-10-11 through Apple Mail,
which quoted every line. Open: Ryan must add the Gmail app password to the
Keychain (command in `analytics/send_report.py`) before the 2026-10-18 run, or
that run alerts him instead of emailing David. `analytics/data/` (history) and `analytics/reports/`
(PDFs) stay local and gitignored because this repo is public.
