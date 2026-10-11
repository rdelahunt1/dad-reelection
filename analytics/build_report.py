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
    wk = raw["week"]
    first = date.fromisoformat(wk["from"])
    week_days = {(first + timedelta(i)).isoformat() for i in range(7)}
    daily_sum = sum(n for k, n in raw["history_pageviews"] if k in week_days)
    if daily_sum != wk["pageviews"]:
        problems.append(f"daily pageviews sum {daily_sum} != week total {wk['pageviews']}")
    page_sum = sum(p["count"] for p in wk["pages"])
    if abs(page_sum - wk["pageviews"]) > 2:
        problems.append(f"page counts sum {page_sum} != week total {wk['pageviews']}")
    if problems:
        sys.exit("DATA CHECK FAILED: " + "; ".join(problems))


# ---------- rendering ----------

def d(iso):
    return date.fromisoformat(iso)


def bars(points, height, width=680, label_every=1, small=False):
    """points: [(label, value, emphasized)]"""
    n = len(points)
    top = max([v for _, v, _ in points] + [1])
    pad = 18 if small else 0
    slot = (width - 2 * pad) / n
    bw = min(54, slot * (0.75 if small else 0.64))
    s = [f'<svg viewBox="0 0 {width} {height + 34}" width="100%" role="img">',
         f'<line x1="0" y1="{height}" x2="{width}" y2="{height}" stroke="#cfc8b9"/>']
    for i, (lab, v, emph) in enumerate(points):
        h = max(2, v / top * (height - 22))
        x = pad + i * slot + (slot - bw) / 2
        fill = RED if emph else NAVY
        s.append(f'<rect x="{x:.1f}" y="{height - h:.1f}" width="{bw:.1f}" height="{h:.1f}" rx="3" fill="{fill}"/>')
        if not small:
            s.append(f'<text x="{x + bw / 2:.1f}" y="{height - h - 6:.1f}" text-anchor="middle" font-size="11" fill="{INK}">{v:,}</text>')
        if (small and emph) or (not small and (i % label_every == 0 or i == n - 1)):
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


def page_history(files):
    """{week_start_iso: {page_label: pageviews}} from every capture's week and prev_week."""
    out = {}
    for fpath in files:
        raw = json.loads(fpath.read_text())
        for key in ("prev_week", "week"):
            out[raw[key]["from"]] = group(raw[key]["pages"], page_label)
    return dict(sorted(out.items()))


def appendix(days, files, wk_from):
    weeks = weekly_totals(days)[-16:]
    week_vis = {}
    for fpath in files:
        r = json.loads(fpath.read_text())
        for key in ("prev_week", "week"):
            week_vis[r[key]["from"]] = r[key]["visitors"]
    rows, prev = [], None
    for s, pv, vis in weeks:
        keys = [(s + timedelta(i)).isoformat() for i in range(7)]
        busiest = max(keys, key=lambda k: days[k]["pageviews"])
        mark = ' class="cur"' if s.isoformat() == wk_from else ""
        rows.append(f'<tr{mark}><td>{s:%b %-d} – {s + timedelta(6):%b %-d}</td><td class="n">{pv:,}</td>'
                    f'<td class="n">{f"{week_vis[s.isoformat()]:,}" if s.isoformat() in week_vis else "–"}</td><td class="c">{change(pct(pv, prev)) if prev else ""}</td>'
                    f'<td class="c">{d(busiest):%a %b %-d} ({days[busiest]["pageviews"]})</td></tr>')
        prev = pv
    keys = sorted(days)[-84:]
    daily = [(d(k).strftime("%b %-d").upper(), days[k]["pageviews"], d(k).weekday() == 6) for k in keys]
    chart = bars(daily, 90, label_every=7, small=True)

    ph = page_history(files)
    cols = list(ph)[-6:]
    labels = sorted({l for c in cols for l in ph[c]}, key=lambda l: -sum(ph[c].get(l, 0) for c in cols))
    head = "".join(f'<th class="n">{d(c):%b %-d}</th>' for c in cols)
    body = "".join(f'<tr><td>{html.escape(l)}</td>' + "".join(f'<td class="n">{ph[c].get(l, 0) or "–"}</td>' for c in cols) + "</tr>"
                   for l in labels)
    return f"""
<div class="appendix">
<div class="ref"><div class="tag">EXTRA DETAIL · OPTIONAL READING</div><b>You can stop here.</b> Everything you need is on page 1. The pages below are the full
traffic history, kept here in case you ever want to dig into the details. Feel free to skip them.</div>
<section><div class="h"><h2>Every day on record</h2><span>Pageviews per day, last {len(keys)} days · red bars = Sundays (labeled)</span></div>{chart}</section>
<section><div class="h"><h2>Week by week</h2><span>Sun–Sat weeks · highlighted = this report · visitors shown for weeks captured since reports began</span></div>
<table class="small"><tr><th>Week</th><th class="n">Pageviews</th><th class="n">Visitors</th><th class="c">Change</th><th class="c">Busiest day</th></tr>{"".join(reversed(rows))}</table></section>
<section><div class="h"><h2>Pages read, by week</h2><span>Pageviews · column = week starting · weeks captured since reports began</span></div>
<table class="small"><tr><th>Page</th>{head}</tr>{body}</table></section>
</div>"""


def render(raw, days, f, takeaways, files):
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
.appendix {{ break-before: page; padding: 26px 40px 0; font-size: 9.5px; }}
.ref {{ background: {CREAM}; border: 1px dashed #b9b1a0; border-radius: 6px; padding: 10px 14px; color: {MUTED}; font-size: 10.5px; line-height: 1.45; }}
.ref b {{ color: {INK}; }}
.ref .tag {{ font-size: 8.5px; letter-spacing: .12em; font-weight: 700; color: {RED}; margin-bottom: 3px; }}
table.small td, table.small th {{ padding: 3px 0; font-size: 9.5px; }}
table.small th {{ text-align: left; font-weight: 600; color: {MUTED}; border-bottom: 1px solid {RULE}; }}
table.small th.n, table.small th.c {{ text-align: right; }}
table.small td.c {{ width: auto; }}
tr.cur td {{ background: #fbf3e6; font-weight: 600; }}
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
{appendix(days, files, wk["from"])}
</body></html>"""


def email_text(raw, f, takeaways):
    wk = raw["week"]
    p = f["pageviews_change_pct"]
    trend = "" if p is None else f" ({'up' if p >= 0 else 'down'} {abs(p)}% from the week before)"
    items = "\n\n".join(f"{i}. {t['title']} {t['detail']}" for i, t in enumerate(takeaways, 1))
    return (f"Hi Dad,\n\nHere is the campaign website report for {d(wk['from']):%b %-d} – {d(wk['to']):%b %-d}: "
            f"{f['pageviews']:,} pageviews from {f['visitors']:,} visitors{trend}.\n\nBig takeaways\n\n{items}\n\n"
            "The full report is attached.\n\nRyan\n\n"
            "(Sent automatically every Sunday from Netlify Web Analytics for delahuntforcommissioner.com.)\n")


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
    html_path.write_text(render(raw, days, f, json.loads(tk.read_text()), files))
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={pdf_path}", html_path.as_uri()], check=True, capture_output=True)
    takeaways = json.loads(tk.read_text())
    (REPORTS / f"{name}-email.txt").write_text(email_text(raw, f, takeaways))
    pages = subprocess.run(["pdfinfo", str(pdf_path)], capture_output=True, text=True).stdout
    print(pdf_path)
    print(REPORTS / f"{name}-email.txt")
    print("subject: Campaign website report: " + f"{d(raw['week']['from']):%b %-d} – {d(raw['week']['to']):%b %-d}")
    print("pages:", re.search(r"Pages:\s+(\d+)", pages).group(1))


if __name__ == "__main__":
    main()
