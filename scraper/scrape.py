"""Scrapes Transport Canada's drone flight school table and records what's new."""
import json, re, sys, datetime, pathlib

URL = "https://tc.canada.ca/en/aviation/drone-safety/drone-pilot-licensing/find-drone-flight-school"
DATA = pathlib.Path("docs/schools.json")
NEW_MD = pathlib.Path("new_schools.md")

# Preferred: ask the page's own DataTable for every row, even ones on other pages.
JS_API = """() => {
  const clean = h => { const d = document.createElement('div'); d.innerHTML = String(h ?? ''); return d.textContent.replace(/\\s+/g,' ').trim(); };
  if (!(window.jQuery && jQuery.fn.dataTable)) return null;
  for (const t of jQuery('table').toArray()) {
    if (!jQuery.fn.dataTable.isDataTable(t)) continue;
    const rows = jQuery(t).DataTable().rows().data().toArray();
    if (rows.length) return rows.map(r => (Array.isArray(r) ? r : Object.values(r)).map(clean));
  }
  return null;
}"""

# Fallback: plain table rows in the page after showing the largest page size.
JS_DOM = """() => {
  const clean = h => h.textContent.replace(/\\s+/g,' ').trim();
  const sel = document.querySelector('select[name$="_length"]');
  if (sel) { sel.value = sel.options[sel.options.length-1].value; sel.dispatchEvent(new Event('change', {bubbles:true})); }
  return [...document.querySelectorAll('table tbody tr')].map(tr => [...tr.querySelectorAll('td')].map(clean)).filter(r => r.length);
}"""

def norm(s):
    return re.sub(r"\s+", " ", s.lower()).strip()

def fetch_rows():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--disable-blink-features=AutomationControlled"])
        ctx = b.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            locale="en-CA", timezone_id="America/Vancouver",
            viewport={"width": 1366, "height": 900})
        page = ctx.new_page()
        resp = page.goto(URL, wait_until="networkidle", timeout=90000)
        print("HTTP status:", resp.status if resp else None)
        try:
            page.wait_for_selector("table tbody tr td", timeout=60000)
        except Exception:
            pass
        page.wait_for_timeout(2000)
        rows = page.evaluate(JS_API)
        if not rows:
            rows = page.evaluate(JS_DOM)
            page.wait_for_timeout(1000)
            rows = page.evaluate(JS_DOM)
        pathlib.Path("debug.html").write_text(page.content(), encoding="utf-8")
        b.close()
    return [{"name": r[0], "areas": ", ".join(r[1:]).strip()} for r in rows if r and r[0]]

def merge(prev, rows, today, now):
    old = {norm(s["name"]): s for s in prev.get("schools", [])}
    first = not old
    seen, schools, added = set(), [], []
    for r in rows:
        k = norm(r["name"])
        if k in seen:
            continue
        seen.add(k)
        if k in old:
            s = old[k]; s["areas"] = r["areas"] or s["areas"]; s["name"] = r["name"]
        else:
            s = {"name": r["name"], "areas": r["areas"], "firstSeen": None if first else today}
            if not first: added.append(s)
        s["lastSeen"] = today
        schools.append(s)
    removed = prev.get("removed", [])
    gone = [dict(name=s["name"], areas=s["areas"], removedOn=today) for k, s in old.items() if k not in seen]
    removed = (gone + removed)[:50]
    schools.sort(key=lambda s: s["name"].lower())
    out = {"lastChecked": now, "lastChanged": today if (added or gone) else prev.get("lastChanged"),
           "count": len(schools), "baseline": first or prev.get("baseline", False) and not added,
           "schools": schools, "removed": removed}
    return out, added, gone

def main():
    rows = fetch_rows()
    if not rows:
        print("No rows found; leaving data untouched."); sys.exit(1)
    prev = json.loads(DATA.read_text()) if DATA.exists() else {}
    if prev.get("count") and len(rows) < prev["count"] * 0.5:
        print(f"Only {len(rows)} rows vs {prev['count']} before; looks like a scrape problem."); sys.exit(1)
    now = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    out, added, gone = merge(prev, rows, now[:10], now)
    DATA.parent.mkdir(exist_ok=True)
    DATA.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{len(rows)} schools, {len(added)} new, {len(gone)} removed")
    if added:
        NEW_MD.write_text("New drone flight schools on Transport Canada’s list:\n\n" +
            "\n".join(f"- **{s['name']}** — {s['areas'] or 'no area listed'}" for s in added) + f"\n\n[Full list]({URL})\n", encoding="utf-8")

if __name__ == "__main__":
    main()
