// Run with the browser pane's javascript_tool on any app.netlify.com page while signed in.
// Returns one JSON string with everything build_report.py needs; save it to data/raw/<today>.json.
// Report week = the last 7 complete days, Sunday through Saturday, in the browser's local time.
await (async () => {
  const SITE = "19b87917-6544-4a94-8bf0-e743ac2836cc"; // delahuntforcommissioner.com
  const base = `/access-control/analytics-api/v2/${SITE}/`;
  const off = -new Date().getTimezoneOffset();
  const tz = (off >= 0 ? "+" : "-") + String(Math.floor(Math.abs(off) / 60)).padStart(2, "0") + String(Math.abs(off) % 60).padStart(2, "0");
  const midnight = (d) => { const x = new Date(d); x.setHours(0, 0, 0, 0); return x; };
  const today = midnight(new Date());
  const weekEnd = new Date(today); weekEnd.setDate(today.getDate() - today.getDay()); // most recent Sunday 00:00 = end of last Sat
  const weekStart = new Date(weekEnd); weekStart.setDate(weekEnd.getDate() - 7);
  const prevStart = new Date(weekStart); prevStart.setDate(weekStart.getDate() - 7);
  const histStart = new Date(today); histStart.setDate(today.getDate() - 120);
  const get = async (path, from, to, extra = "") => {
    const r = await fetch(`${base}${path}?from=${+from}&to=${+to - 1}&timezone=${tz}${extra}`, { credentials: "include" });
    if (!r.ok) throw new Error(`${path} HTTP ${r.status}`);
    return (await r.json()).data;
  };
  const iso = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  const days = (rows) => rows.map(([t, n]) => [iso(new Date(t)), n]);
  const range = async (from, to) => ({
    from: iso(from), to: iso(new Date(+to - 1)),
    pageviews: (await get("pageviews", from, to, "&resolution=range"))[0]?.[1] ?? 0,
    visitors: (await get("visitors", from, to, "&resolution=range"))[0]?.[1] ?? 0,
    pages: await get("ranking/pages", from, to, "&limit=30"),
    sources: await get("ranking/sources", from, to, "&limit=15"),
    countries: await get("ranking/countries", from, to),
  });
  return JSON.stringify({
    captured_at: new Date().toISOString(),
    timezone: tz,
    week: await range(weekStart, weekEnd),
    prev_week: await range(prevStart, weekStart),
    history_pageviews: days(await get("pageviews", histStart, today, "&resolution=day")),
    history_visitors: days(await get("visitors", histStart, today, "&resolution=day")),
  });
})();
