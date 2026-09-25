#!/usr/bin/env python3
"""Regenerate the sentences in each guide that quote counts from the built data,
so the guide cannot drift from the dataset it describes (the audit found stale
routing, facility and cell counts).

    python3 scripts/sync_guide_facts.py          # rewrite cities/*/guide.html
    python3 scripts/sync_guide_facts.py --check  # exit 1 if any guide is stale

Each generated sentence sits in <span data-fact="NAME" [data-extra="..."]>…</span>;
only the span's text is replaced. data-extra is a city-specific aside kept verbatim."""
import html, json, re, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SLUGS = re.findall(r"slug:'([a-z0-9-]+)'", (ROOT / "app" / "cities.js").read_text())
KIND = {"contracosta": "county", "bakersfield": "city", "sanramon": "city"}


def n(v): return f"{v:,}"


def facts(slug):
    d = ROOT / "cities" / slug / "data"
    P = [f["properties"] for f in json.loads((d / f"{slug}.geojson").read_text())["features"]]
    res = [p for p in P if p["place"] == "res"]
    place = Counter(p["place"] for p in P)
    src = Counter(p.get("access_src") for p in P)
    src_res = Counter(p.get("access_src") for p in res)
    appr = sum(1 for p in res if p.get("access_quality") == "approach-review")
    sites = len(json.loads((d / f"centers_{slug}.geojson").read_text())["features"])
    kind = KIND.get(slug, "study-area")
    sl = src.get("straightline", 0)
    routing = (f"Of the {n(len(P))} cells in the current overlay CSV, {n(src.get('routed', 0))} are routed"
               + (f" and {n(sl)} use the straight-line fallback ({n(src_res.get('straightline', 0))} of them ranked residential areas)" if sl else "; none uses the straight-line fallback")
               + f"; {n(appr)} ranked areas carry an approach-review flag because the cell-to-network connection exceeds 100 m.")
    return {
        "cooling-sites": f"The {kind} file contains {n(sites)} mapped sites across library, community center, pool and senior/shelter categories",
        "cooling-sites-used": f"Walking estimates still use the {n(sites)} discovery sites, not just the official directory.",
        "access-routing": routing,
        "place-counts": (f"Current build: {n(place.get('res', 0))} residential, {n(place.get('activity', 0))} developed without residents "
                         f"and {n(place.get('empty', 0))} undeveloped cells{{extra}}, totaling {n(len(P))}."),
    }


SPAN = re.compile(r'<span data-fact="([a-z-]+)"(?: data-extra="([^"]*)")?>(.*?)</span>', re.S)


def render(slug):
    path = ROOT / "cities" / slug / "guide.html"
    src = path.read_text()
    F = facts(slug)
    seen = set()

    def sub(m):
        name, extra, _ = m.group(1), m.group(2), m.group(3)
        seen.add(name)
        text = F[name].replace("{extra}", (" " + html.unescape(extra)) if extra else "")
        return f'<span data-fact="{name}"' + (f' data-extra="{extra}"' if extra else "") + f'>{html.escape(text, quote=False)}</span>'
    out = SPAN.sub(sub, src)
    missing = {"access-routing", "place-counts", "cooling-sites"} - seen
    assert not missing, f"{slug}: guide lacks data-fact spans {sorted(missing)}"
    return path, src, out


def main():
    check = "--check" in sys.argv
    stale = 0
    for slug in SLUGS:
        path, old, new = render(slug)
        if old != new:
            stale += 1
            if check:
                print(f"stale: {path.relative_to(ROOT)}", file=sys.stderr)
            else:
                path.write_text(new)
    if check and stale:
        sys.exit(f"{stale} guide(s) quote counts that differ from the data; run scripts/sync_guide_facts.py")
    print("guide facts: all current" if check else f"rewrote: {stale} guide(s)")


if __name__ == "__main__":
    main()
