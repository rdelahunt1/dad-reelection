// Run with the browser pane's javascript_tool on any app.netlify.com page while signed in.
// Returns one JSON string with everything build_report.py needs; save it to data/raw/<today CT>.json.
// Report week = the last 7 complete days, Sunday through Saturday, in Central time (America/Chicago),
// whatever time zone the Mac is in. One fixed UTC offset (CT's offset right now) is used for every
// day boundary so the dates match Netlify's daily buckets.
await (async () => {
  const SITE = "19b87917-6544-4a94-8bf0-e743ac2836cc"; // delahuntforcommissioner.com
  const base = `/access-control/analytics-api/v2/${SITE}/`;
  const ct = Object.fromEntries(new Intl.DateTimeFormat("en-US", { timeZone: "America/Chicago", hourCycle: "h23",
    year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" })
    .formatToParts(new Date()).filter((p) => p.type !== "literal").map((p) => [p.type, +p.value]));
  const now = new Date(); now.setSeconds(0, 0);
  const off = Math.round((Date.UTC(ct.year, ct.month - 1, ct.day, ct.hour, ct.minute) - now) / 60000); // e.g. -300
  const tz = (off >= 0 ? "+" : "-") + String(Math.floor(Math.abs(off) / 60)).padStart(2, "0") + String(Math.abs(off) % 60).padStart(2, "0");
  const day = (k) => new Date(Date.UTC(ct.year, ct.month - 1, ct.day + k) - off * 60000); // CT midnight, k days from today
  const dow = new Date(Date.UTC(ct.year, ct.month - 1, ct.day)).getUTCDay();
  const today = day(0);
  const weekEnd = day(-dow); // most recent Sunday 00:00 CT = end of last Sat
  const weekStart = day(-dow - 7);
  const prevStart = day(-dow - 14);
  const histStart = day(-120);
  const get = async (path, from, to, extra = "") => {
    const r = await fetch(`${base}${path}?from=${+from}&to=${+to - 1}&timezone=${tz}${extra}`, { credentials: "include" });
    if (!r.ok) throw new Error(`${path} HTTP ${r.status}`);
    return (await r.json()).data;
  };
  const iso = (d) => new Date(+d + off * 60000).toISOString().slice(0, 10); // date in CT
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
    timezone_name: "America/Chicago",
    week: await range(weekStart, weekEnd),
    prev_week: await range(prevStart, weekStart),
    history_pageviews: days(await get("pageviews", histStart, today, "&resolution=day")),
    history_visitors: days(await get("visitors", histStart, today, "&resolution=day")),
  });
})();
