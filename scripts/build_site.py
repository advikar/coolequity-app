"""Assemble the static site into dist/ (or the directory given with --out).

    python3 scripts/build_site.py            # -> dist/
    python3 scripts/build_site.py --serve    # build, then serve on http://localhost:8000/

Layout of the result, which is exactly what GitHub Pages serves:

    index.html                 chooser (site/index.html)
    vendor/                    fonts for the chooser
    <slug>/app/                app/* (shared) + cities/<slug>/{city.js,guide.html,cooling.html}
    <slug>/data/               the three files the map fetches, from cities/<slug>/data/

Nothing is generated or rewritten: every file is a byte-for-byte copy, so what you
test locally is what deploys. Standard library only.
"""
import argparse
import http.server
import re
import shutil
import sys
from functools import partial
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP_FILES = ["index.html", "guide.css", "guide.js", "cities.js", "vendor"]
CITY_PAGES = ["city.js", "guide.html", "cooling.html"]
DATA_FILES = ["{slug}.geojson", "centers_{slug}.geojson", "boundary_{slug}.geojson", "designated_{slug}.geojson"]


def listed_cities():
    """Slugs in app/cities.js, in order. The build refuses if they and cities/ disagree."""
    text = (ROOT / "app" / "cities.js").read_text()
    return re.findall(r"slug:'([a-z0-9-]+)'", text)


def build(out: Path) -> list[str]:
    slugs = listed_cities()
    folders = sorted(p.name for p in (ROOT / "cities").iterdir() if (p / "city.js").exists())
    if sorted(slugs) != folders:
        sys.exit(f"app/cities.js lists {sorted(slugs)} but cities/ has {folders}")
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    shutil.copy2(ROOT / "site" / "index.html", out / "index.html")
    shutil.copytree(ROOT / "app" / "vendor", out / "vendor")
    (out / ".nojekyll").touch()   # Pages would otherwise drop underscore-prefixed paths
    for slug in slugs:
        city = ROOT / "cities" / slug
        app, data = out / slug / "app", out / slug / "data"
        app.mkdir(parents=True)
        data.mkdir()
        for name in APP_FILES:
            src = ROOT / "app" / name
            (shutil.copytree if src.is_dir() else shutil.copy2)(src, app / name)
        for name in CITY_PAGES:
            shutil.copy2(city / name, app / name)
        declared = re.search(r"slug:'([a-z0-9-]+)'", (city / "city.js").read_text())
        if not declared or declared.group(1) != slug:
            sys.exit(f"cities/{slug}/city.js declares slug {declared and declared.group(1)!r}")
        for pattern in DATA_FILES:
            name = pattern.format(slug=slug)
            shutil.copy2(city / "data" / name, data / name)
    for path in sorted(out.rglob("*")):
        if path.is_file() and path.stat().st_size == 0 and path.name != ".nojekyll":
            sys.exit(f"empty file in build: {path.relative_to(out)}")
    return slugs


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=ROOT / "dist")
    ap.add_argument("--serve", action="store_true", help="serve the build on --port afterwards")
    ap.add_argument("--port", type=int, default=8000)
    a = ap.parse_args()
    slugs = build(a.out)
    files = sum(1 for p in a.out.rglob("*") if p.is_file())
    print(f"built {len(slugs)} cities ({', '.join(slugs)}), {files} files -> {a.out}")
    if a.serve:
        handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(a.out))
        print(f"serving http://localhost:{a.port}/")
        http.server.ThreadingHTTPServer(("", a.port), handler).serve_forever()


if __name__ == "__main__":
    main()
