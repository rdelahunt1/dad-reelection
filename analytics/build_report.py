#!/usr/bin/env python3
"""Weekly campaign-website traffic report from Netlify Web Analytics.

  python3 analytics/build_report.py stats [DATE]   print this week's facts (for writing takeaways)
  python3 analytics/build_report.py pdf [DATE]     build reports/traffic-summary-DATE.pdf

DATE is the capture date of data/raw/DATE.json (default: newest). Takeaways come from
data/takeaways/DATE.json: [{"title": "...", "detail": "..."}, ...].
Every raw capture is merged into data/daily.csv so history outlives Netlify's retention.
data/ and reports/ are gitignored: the repo is public.
"""
import csv
import html
import json
import re
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW, TAKE, REPORTS = ROOT / "data" / "raw", ROOT / "data" / "takeaways", ROOT / "reports"
DAILY = ROOT / "data" / "daily.csv"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

NAVY, RED, CREAM, INK, MUTED, RULE = "#13294b", "#a3252f", "#f4f1ea", "#1d2533", "#647083", "#e2ddd2"
GREEN = "#2f6b3f"


# ---------- data ----------

def load(date_id=None):
    files = sorted(RAW.glob("*.json"))
    if not files:
        sys.exit(f"no captures in {RAW}")
    path = RAW / f"{date_id}.json" if date_id else files[-1]
    raw = json.loads(path.read_text())
    raw["_id"] = path.stem
    return raw, [f for f in files if f.stem <= path.stem]


def merge_daily(files):
    """date -> {pageviews, visitors}; later captures overwrite earlier ones."""
    days = {}
    if DAILY.exists():
        for r in csv.DictReader(DAILY.open()):
            days[r["date"]] = {"pageviews": int(r["pageviews"]), "visitors": int(r["visitors"]) if r["visitors"] else None}
    for f in files:
        raw = json.loads(f.read_text())
        for d, n in raw["history_pageviews"]:
            days.setdefault(d, {"pageviews": 0, "visitors": None})["pageviews"] = n
        for d, n in raw["history_visitors"]:
            days.setdefault(d, {"pageviews": 0, "visitors": None})["visitors"] = n
    with DAILY.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "pageviews", "visitors"])
        for k in sorted(days):
            w.writerow([k, days[k]["pageviews"], "" if days[k]["visitors"] is None else days[k]["visitors"]])
    return days


def page_label(path):
    slug = re.sub(r"\.html$", "", path).strip("/")
    if slug in ("", "index"):
        return "Home page"
    if slug.startswith("press-release-"):
        return slug[len("press-release-"):].replace("-", " ").capitalize() + " press release"
    return "/" + slug


def source_label(host):
    if not host:
        return "Direct / unattributed"
    if "facebook" in host:
        return "Facebook"
    if host.startswith("google.") or ".google." in host:
        return "Google"
    if "bing" in host:
        return "Bing"
    if "ballotpedia" in host:
        return "Ballotpedia"
    return "Other sites"


def group(rows, labeler):
    out = {}
    for r in rows:
        k = labeler(r["resource"])
        out[k] = out.get(k, 0) + r["count"]
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


def pct(a, b):
    return None if not b else round((a - b) / b * 100)


def weekly_totals(days):
    """Sun–Sat weeks that are fully covered, oldest first: [(start_date, pageviews, visitors|None)]."""
    if not days:
        return []
    first = date.fromisoformat(min(days))
    start = first + timedelta(days=(6 - first.weekday()) % 7)  # first Sunday on/after first day
    out = []
    while True:
        keys = [(start + timedelta(i)).isoformat() for i in range(7)]
        if not all(k in days for k in keys):
            break
        vis = [days[k]["visitors"] for k in keys]
        out.append((start, sum(days[k]["pageviews"] for k in keys), None if None in vis else sum(vis)))
        start += timedelta(7)
    return out


def facts(raw, days):
    wk, pv = raw["week"], raw["prev_week"]
    pages, ppages = group(wk["pages"], page_label), group(pv["pages"], page_label)
    srcs, psrcs = group(wk["sources"], source_label), group(pv["sources"], source_label)
    wdays = [(date.fromisoformat(wk["from"]) + timedelta(i)).isoformat() for i in range(7)]
    best = max(wdays, key=lambda d: days.get(d, {}).get("pageviews", 0))
    us = next((c["count"] for c in wk["countries"] if c["resource"] == "US"), 0)
    weeks = weekly_totals(days)
    return {
        "week": f'{wk["from"]} to {wk["to"]}',
        "pageviews": wk["pageviews"], "pageviews_prev": pv["pageviews"], "pageviews_change_pct": pct(wk["pageviews"], pv["pageviews"]),
        "visitors": wk["visitors"], "visitors_prev": pv["visitors"], "visitors_change_pct": pct(wk["visitors"], pv["visitors"]),
        "daily_pageviews": {d: days.get(d, {}).get("pageviews") for d in wdays},
        "best_day": [best, days.get(best, {}).get("pageviews")],
        "pages_this_week": pages, "pages_prev_week": ppages,
        "sources_this_week": srcs, "sources_prev_week": psrcs,
        "us_share_pct": round(us / wk["pageviews"] * 100) if wk["pageviews"] else None,
        "weekly_pageviews_all_tracked": {s.isoformat(): n for s, n, _ in weeks},
        "best_week_on_record": max(weeks, key=lambda w: w[1])[0].isoformat() if weeks else None,
    }


def validate(raw):
    problems = []
    if raw["week"]["pageviews"] <= 0:
        problems.append("week pageviews is 0")
    if not raw["history_pageviews"]:
        problems.append("no daily history")
    if not raw["week"]["pages"]:
        problems.append("no page rankings")
    if problems:
        sys.exit("DATA CHECK FAILED: " + "; ".join(problems))


# ---------- rendering ----------

def d(iso):
    return date.fromisoformat(iso)


def bars(points, height, width=680, label_every=1, accent_last=False):
    """points: [(label, value, emphasized)]"""
    n = len(points)
    top = max([v for _, v, _ in points] + [1])
    slot = width / n
    bw = min(54, slot * 0.64)
    s = [f'<svg viewBox="0 0 {width} {height + 34}" width="100%" role="img">',
         f'<line x1="0" y1="{height}" x2="{width}" y2="{height}" stroke="#cfc8b9"/>']
    for i, (lab, v, emph) in enumerate(points):
        h = max(2, v / top * (height - 22))
        x = i * slot + (slot - bw) / 2
        fill = RED if emph else NAVY
        s.append(f'<rect x="{x:.1f}" y="{height - h:.1f}" width="{bw:.1f}" height="{h:.1f}" rx="3" fill="{fill}"/>')
        s.append(f'<text x="{x + bw / 2:.1f}" y="{height - h - 6:.1f}" text-anchor="middle" font-size="11" fill="{INK}">{v:,}</text>')
        if i % label_every == 0 or i == n - 1:
            s.append(f'<text x="{x + bw / 2:.1f}" y="{height + 17}" text-anchor="middle" font-size="9.5" '
                     f'letter-spacing=".04em" fill="{MUTED}">{html.escape(lab)}</text>')
    s.append("</svg>")
    return "".join(s)


def change(p, prev=None):
    if p is None:
        return '<span class="flat">new</span>'
    cls = "up" if p > 0 else "down" if p < 0 else "flat"
    arrow = "▲" if p > 0 else "▼" if p < 0 else "•"
    tail = f" vs {prev:,} prior week" if prev is not None else ""
    return f'<span class="{cls}">{arrow} {abs(p)}%</span>{tail}'


def render(raw, days, f, takeaways):
    wk = raw["week"]
    cap = raw["_id"]
    wfrom, wto = d(wk["from"]), d(wk["to"])
    daily = [(d(k).strftime("%a %-d").upper(), v or 0, k == f["best_day"][0]) for k, v in f["daily_pageviews"].items()]
    weeks = weekly_totals(days)
    weekly = [(s.strftime("%b %-d").upper(), n, s.isoformat() == wk["from"]) for s, n, _ in weeks]
    top_page = next(iter(f["pages_this_week"]), "—")

    total = sum(f["pages_this_week"].values()) or 1
    page_rows = "".join(
        f'<tr><td>{html.escape(k)}</td><td class="n">{v:,}</td><td class="p">{round(v / total * 100)}%</td>'
        f'<td class="c">{change(pct(v, f["pages_prev_week"].get(k)) if k in f["pages_prev_week"] else None)}</td></tr>'
        for k, v in f["pages_this_week"].items())
    src_rows = "".join(
        f'<tr><td>{html.escape(k)}</td><td class="n">{v:,}</td>'
        f'<td class="c">{change(pct(v, f["sources_prev_week"].get(k)) if k in f["sources_prev_week"] else None)}</td></tr>'
        for k, v in f["sources_this_week"].items())
    take = "".join(f'<li><b>{html.escape(t["title"])}</b> {html.escape(t["detail"])}</li>' for t in takeaways)

    weekly_block = ""
    if len(weekly) > 1:
        weekly_block = f"""
<section><div class="h"><h2>The trend</h2><span>Pageviews per week (Sun–Sat), every full week on record · red = this report</span></div>
{bars(weekly, 96, label_every=max(1, len(weekly) // 12))}</section>"""

    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>Campaign website traffic | David J. De La Hunt | week of {wfrom:%b %-d, %Y}</title>
<style>
@page {{ size: letter; margin: 0; }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; font-family: "Helvetica Neue", Arial, sans-serif; color: {INK}; font-size: 11.5px; -webkit-print-color-adjust: exact; }}
header {{ background: {NAVY}; color: #fff; padding: 24px 40px 20px; border-left: 10px solid {RED}; }}
header .k {{ display: flex; justify-content: space-between; font-size: 9.5px; letter-spacing: .1em; opacity: .85; }}
header h1 {{ font-weight: 300; font-size: 29px; margin: 8px 0 4px; letter-spacing: -.01em; }}
header .sub {{ font-size: 11px; opacity: .85; }}
main {{ padding: 18px 40px 0; }}
.kpis {{ display: grid; grid-template-columns: 1fr 1fr 1.25fr; gap: 12px; }}
.kpi {{ background: {CREAM}; border-radius: 6px; padding: 12px 14px; }}
.kpi .v {{ font-size: 26px; color: {NAVY}; font-weight: 300; line-height: 1.1; }}
.kpi .v.sm {{ font-size: 16px; font-weight: 400; padding-top: 6px; }}
.kpi .l {{ color: {RED}; font-size: 8.5px; letter-spacing: .1em; margin-top: 5px; font-weight: 600; }}
.kpi .s {{ color: {MUTED}; font-size: 9.5px; margin-top: 3px; }}
.take {{ border-left: 3px solid {RED}; padding: 4px 0 4px 14px; margin: 16px 0 4px; }}
.take h2 {{ margin-bottom: 4px; }}
.take ol {{ margin: 0; padding-left: 16px; }}
.take li {{ margin: 5px 0; line-height: 1.45; }}
.take b {{ color: {NAVY}; }}
section {{ margin-top: 14px; }}
.h {{ display: flex; justify-content: space-between; align-items: baseline; border-bottom: 1px solid {RULE}; padding-bottom: 4px; margin-bottom: 8px; }}
.h span {{ font-size: 9px; color: {MUTED}; }}
h2 {{ font-size: 10px; font-weight: 600; letter-spacing: .1em; text-transform: uppercase; color: {NAVY}; margin: 0; }}
.cols {{ display: grid; grid-template-columns: 1.35fr 1fr; gap: 26px; }}
table {{ width: 100%; border-collapse: collapse; }}
td {{ padding: 5px 0; border-bottom: 1px solid {RULE}; }}
td.n {{ text-align: right; width: 44px; }}
td.p {{ text-align: right; width: 38px; color: {MUTED}; font-size: 9.5px; }}
td.c {{ text-align: right; width: 64px; font-size: 9.5px; color: {MUTED}; }}
.up {{ color: {GREEN}; }} .down {{ color: {RED}; }} .flat {{ color: {MUTED}; }}
.kpi .s .up, .kpi .s .down {{ font-weight: 600; }}
.foot {{ margin: 14px 40px 0; border-top: 1px solid {RULE}; padding-top: 7px; font-size: 8.5px; color: {MUTED}; line-height: 1.5; }}
</style></head><body>
<header><div class="k"><span>CAMPAIGN WEBSITE · WEEKLY REPORT</span><span>{wfrom:%b %-d} – {wto:%b %-d, %Y}</span></div>
<h1>Weekly website traffic</h1><div class="sub">David J. De La Hunt &nbsp;|&nbsp; Hubbard County Commissioner, District 1 &nbsp;|&nbsp; delahuntforcommissioner.com</div></header>
<main>
<div class="kpis">
<div class="kpi"><div class="v">{f['pageviews']:,}</div><div class="l">PAGEVIEWS</div><div class="s">{change(f['pageviews_change_pct'], f['pageviews_prev'])}</div></div>
<div class="kpi"><div class="v">{f['visitors']:,}</div><div class="l">UNIQUE VISITORS</div><div class="s">{change(f['visitors_change_pct'], f['visitors_prev'])}</div></div>
<div class="kpi"><div class="v sm">{html.escape(top_page)}</div><div class="l">MOST-READ PAGE</div><div class="s">{f['pages_this_week'].get(top_page, 0):,} pageviews · {round(f['pages_this_week'].get(top_page, 0) / total * 100)}% of all views</div></div>
</div>
<div class="take"><h2>Big takeaways</h2><ol>{take}</ol></div>
<section><div class="h"><h2>Day by day</h2><span>Pageviews · red = busiest day</span></div>
{bars(daily, 120)}</section>
{weekly_block}
<div class="cols">
<section><div class="h"><h2>What people read</h2><span>Pageviews · share · vs prior week</span></div><table>{page_rows}</table></section>
<section><div class="h"><h2>How they found the site</h2><span>Visits · vs prior week</span></div><table>{src_rows}</table></section>
</div>
</main>
<div class="foot">How to read this: a pageview is one page loaded; unique visitors are estimated from IP addresses, not verified people.
"Direct / unattributed" covers typed addresses, bookmarks, texts, emails, and apps that hide the link source.
Both URL forms of each page are combined. {f['us_share_pct']}% of this week's pageviews came from the United States; the rest came from other countries.
<br>Source: Netlify Web Analytics, captured {d(cap):%b %-d, %Y}. Prepared automatically each Sunday.</div>
</body></html>"""


def email_html(raw, f, takeaways):
    wk = raw["week"]
    items = "".join(f"<li style=\"margin:0 0 8px\"><b>{html.escape(t['title'])}</b> {html.escape(t['detail'])}</li>" for t in takeaways)
    p = f["pageviews_change_pct"]
    trend = "" if p is None else f" ({'up' if p >= 0 else 'down'} {abs(p)}% from the week before)"
    return (f'<div style="font-family:Helvetica,Arial,sans-serif;font-size:15px;line-height:1.5;color:#1d2533;max-width:560px">'
            f'<p>Hi Dad,</p><p>Here is the campaign website report for {d(wk["from"]):%b %-d} – {d(wk["to"]):%b %-d}: '
            f'<b>{f["pageviews"]:,} pageviews</b> from <b>{f["visitors"]:,} visitors</b>{trend}.</p>'
            f'<p style="margin-bottom:6px"><b>Big takeaways</b></p><ol style="padding-left:20px;margin-top:0">{items}</ol>'
            f'<p>The full one-page report is attached.</p><p>Ryan</p>'
            f'<p style="font-size:12px;color:#647083">Sent automatically every Sunday from Netlify Web Analytics for delahuntforcommissioner.com.</p></div>')


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "pdf"
    raw, files = load(sys.argv[2] if len(sys.argv) > 2 else None)
    validate(raw)
    days = merge_daily(files)
    f = facts(raw, days)
    if cmd == "stats":
        print(json.dumps(f, indent=1))
        return
    tk = TAKE / f"{raw['_id']}.json"
    if not tk.exists():
        sys.exit(f"missing takeaways file {tk}")
    REPORTS.mkdir(exist_ok=True)
    name = f"traffic-summary-{raw['week']['from']}-to-{raw['week']['to']}"
    html_path, pdf_path = REPORTS / f"{name}.html", REPORTS / f"{name}.pdf"
    html_path.write_text(render(raw, days, f, json.loads(tk.read_text())))
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={pdf_path}", html_path.as_uri()], check=True, capture_output=True)
    takeaways = json.loads(tk.read_text())
    (REPORTS / f"{name}-email.html").write_text(email_html(raw, f, takeaways))
    pages = subprocess.run(["pdfinfo", str(pdf_path)], capture_output=True, text=True).stdout
    print(pdf_path)
    print(REPORTS / f"{name}-email.html")
    print("subject: Campaign website report: " + f"{d(raw['week']['from']):%b %-d} – {d(raw['week']['to']):%b %-d}")
    print("pages:", re.search(r"Pages:\s+(\d+)", pages).group(1))


if __name__ == "__main__":
    main()
