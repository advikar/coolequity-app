# CoolEquity — agent instructions

Read `README.md` (layout) and `HANDOFF.md` before project work. Before editing, record the task,
owner, intended files and next checkpoint in `HANDOFF.md`; update it after each tested
checkpoint and before stopping. Report the tests actually run. Never mark untested behaviour
verified.

## One codebase, one folder per city

- Code in `app/`, `pipeline/`, `scripts/` and `tests/` is shared. A change there applies to
  every city: run `scripts/test.sh` (all cities), not a single-city check.
- Anything city-specific belongs in `cities/<slug>/`. Do not add `if slug == …` branches to
  shared code; add a setting to the city's `config.py` or `city.js` instead.
- The weights in `cities/<slug>/config.py` and `cities/<slug>/city.js` must stay equal; the
  test enforces it.

## Documentation

When changing product features or data behaviour, update the affected city's docs in
`cities/<slug>/` (and `cities/contracosta/FEATURES.md` / `DATA_QUALITY.md`, the reference
audit) in the same change. Keep current behaviour distinct from historical audit notes. Each
city's `guide.html` is the user-facing statement of sources and methods and must agree with
the implementation and that city's current data. Do not describe estimates or planning
assumptions as directly measured facts.

## Git and deploy

All commits are authored by `advikar <70820122+advikar@users.noreply.github.com>`, with no
co-author or tool attribution lines. A push to `main` deploys the site after CI passes, so
push only tested work.
