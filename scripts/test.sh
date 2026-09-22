#!/usr/bin/env bash
# Every check, for every city: the map-page contract (Node built-ins only), the
# pipeline data contracts (needs the Python requirements), a clean site build,
# and whitespace errors in the working tree.
#   scripts/test.sh              all cities
#   scripts/test.sh bakersfield  one city
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
PY="${PYTHON:-$( [ -x .venv/bin/python ] && echo .venv/bin/python || echo python3 )}"
CITIES=("$@")
if [ ${#CITIES[@]} -eq 0 ]; then
  CITIES=($(sed -n "s/.*slug:'\([a-z0-9-]*\)'.*/\1/p" app/cities.js))
fi

node tests/ui-contract.cjs "${CITIES[@]}"
python3 scripts/sync_column_key.py --check
for city in "${CITIES[@]}"; do
  echo; echo "== pipeline data contracts: $city"
  COOLEQUITY_CITY="$city" "$PY" -m unittest discover -s tests -p 'test_*.py'
done
echo
"$PY" scripts/build_site.py --out "$(mktemp -d)/dist"
git diff --check
echo "all checks passed"
