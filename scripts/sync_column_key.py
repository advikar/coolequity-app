#!/usr/bin/env python3
"""Regenerate every guide's export "Column key" table from FIELD_KEY in
app/index.html, so the documentation cannot drift from the exporter.

    python3 scripts/sync_column_key.py          # rewrite cities/*/guide.html
    python3 scripts/sync_column_key.py --check  # exit 1 if any guide is stale

The table sits between <!-- column-key --> and <!-- /column-key --> in each
guide; the script replaces exactly that span. The first column is the CSV
header, the second the JSON key, the third the meaning, all from FIELD_KEY."""
import html, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "app" / "index.html"


def field_key() -> list[tuple[str, str, str]]:
    src = APP.read_text()
    m = re.search(r"const FIELD_KEY=\{(.*?)\n\};", src, re.S)
    assert m, "FIELD_KEY not found"
    rows = []
    for key, col, desc in re.findall(r"(\w+):\['([^']*)','((?:[^'\\]|\\.)*)'\]", m.group(1)):
        rows.append((key, col, desc.replace("\\'", "'")))
    assert len(rows) >= 50, len(rows)
    return rows


def table() -> str:
    body = "".join(f"<tr><td><code>{html.escape(c)}</code></td><td><code>{html.escape(k)}</code></td>"
                   f"<td>{html.escape(d)}</td></tr>" for k, c, d in field_key())
    return ("<!-- column-key --><div class=\"table-wrap\"><table class=\"fields\"><thead><tr><th>Spreadsheet column</th>"
            "<th>JSON key</th><th>Meaning</th></tr></thead><tbody>" + body + "</tbody></table></div><!-- /column-key -->")


def main() -> int:
    check = "--check" in sys.argv
    new = table()
    stale = []
    for g in sorted(ROOT.glob("cities/*/guide.html")):
        text = g.read_text()
        if "<!-- column-key -->" not in text:
            # first run: wrap the existing table
            text, n = re.subn(r'<div class="table-wrap"><table class="fields">.*?</table></div>',
                              new.replace("\\", "\\\\"), text, count=1, flags=re.S)
            assert n == 1, g
        else:
            text2 = re.sub(r"<!-- column-key -->.*?<!-- /column-key -->", lambda _: new, text, count=1, flags=re.S)
            if text2 == text:
                continue
            text = text2
        stale.append(g)
        if not check:
            g.write_text(text)
    if check and stale:
        print("stale column key in: " + ", ".join(str(p.relative_to(ROOT)) for p in stale))
        return 1
    print(f"{'stale' if check else 'rewrote'}: {len(stale)} guide(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
