"""Machine-written provenance for every fetched input.

Each pipeline stage that pulls data from outside the repository calls
record() once per thing it fetched. The entries live in
cities/<slug>/data/sources.json and are rendered to SOURCES.md beside it,
so the human-readable file can never drift from what was actually fetched.
Nobody edits either file by hand.

    from sources import record
    record("04c_wards", "Council wards", url, path=C.WARDS_FILE, count=7,
           publisher="City of Bakersfield GIS Office", note="2022 map 5B")
"""
import datetime
import hashlib
import json
from pathlib import Path

import config as C

JSON_FILE = C.DATA / "sources.json"
MD_FILE = C.DATA / "SOURCES.md"


def sha256_12(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:12]


def _load():
    try:
        return json.loads(JSON_FILE.read_text())
    except (OSError, ValueError):
        return {"city": C.SLUG, "entries": []}


def record(stage, what, url, path=None, count=None, publisher=None, note=None, retrieved=None):
    """Upsert one provenance entry keyed by (stage, what) and re-render SOURCES.md."""
    doc = _load()
    entry = {
        "stage": stage, "what": what, "url": url, "publisher": publisher,
        "retrieved": retrieved or datetime.date.today().isoformat(),
        "count": count, "note": note,
        "file": str(Path(path).relative_to(C.DATA)) if path else None,
        "sha256_12": sha256_12(path) if path and Path(path).exists() else None,
    }
    doc["entries"] = [e for e in doc["entries"] if not (e["stage"] == stage and e["what"] == what)] + [entry]
    doc["entries"].sort(key=lambda e: (e["stage"], e["what"]))
    JSON_FILE.write_text(json.dumps(doc, indent=1) + "\n")
    render(doc)
    return entry


def render(doc=None):
    doc = doc or _load()
    rows = ["| Stage | What | Publisher | Retrieved | Records | File | Hash |", "|---|---|---|---|---|---|---|"]
    for e in doc["entries"]:
        rows.append("| `{stage}` | [{what}]({url}) | {pub} | {ret} | {cnt} | {file} | `{h}` |".format(
            stage=e["stage"], what=e["what"], url=e["url"], pub=e.get("publisher") or "",
            ret=e.get("retrieved") or "", cnt="" if e.get("count") is None else e["count"],
            file=("`%s`" % e["file"]) if e.get("file") else "", h=e.get("sha256_12") or ""))
    notes = [f"- **{e['what']}**: {e['note']}" for e in doc["entries"] if e.get("note")]
    MD_FILE.write_text(
        f"# Sources fetched for {C.CITY}\n\n"
        "Written by the pipeline, one line per fetched input: where it came from, when, how\n"
        "many records, and a fingerprint of the committed file. Do not edit by hand; rerun the\n"
        "stage instead. Hashes are the first 12 hex digits of the file's SHA-256.\n\n"
        + "\n".join(rows) + "\n"
        + ("\n## Notes\n\n" + "\n".join(notes) + "\n" if notes else ""))
