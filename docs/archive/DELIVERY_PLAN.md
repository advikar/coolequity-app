# Cool Equity delivery and model handoff plan

Prepared September 8, 2026 from the local Contra Costa checkout. This is a plan,
not a certification or completed release. Product/data behavior is unchanged.

## Recommendation

Allocate roughly 80–90% of implementation work to Claude and 10–20% to Astra.
These are work-allocation targets, not predicted token usage. Opus is the default
implementer; Sonnet handles bounded changes with clear acceptance checks; Fable
handles difficult methodology, architecture and persistent failures. Astra owns
visual direction and a small number of independent milestone reviews. Every role
has a substitute; no milestone requires one particular provider.

For the user's two projects, provisionally reserve about two thirds of Fable work
for Foster Connect and one third for Cool Equity. Foster Connect likely has more
application engineering if its AI integration and user input require persistence,
authorization, validation, abuse controls, AI evaluation and backend operations.
That comparison is based on the user's description, not a Foster Connect code audit.
Cool Equity has the harder geospatial/provenance and scientific-claims problem.
Additional reasoning cannot substitute for missing field validation or source data.

Fable should first receive one bounded trial here: review the current data-to-UI
contract and identify evidence-backed release blockers. Judge it by correct findings,
useful patches, verification and usage consumed, rather than model reputation.

Anthropic's September 8 documentation says Max includes Fable usage up to 50% of
the regular weekly allowance, that Fable consumes it faster, and that this is not
an additional allowance. Switching to Opus/Sonnet helps at the Fable-specific cap
only if regular Claude allowance remains. Source:
https://support.claude.com/en/articles/15424964-claude-fable-models-on-your-plan

## Observed baseline

- Branch: `contra-costa`; HEAD at inspection: `0350f8a`.
- Substantial pre-existing modified and untracked product/data/test files. Preserve
  them; do not reset, clean, replace them with HEAD, or infer ownership from git status.
- Latest local work includes ACS 2024, canopy coverage/source safeguards, housing-
  weighted LACE, conditional planting scenarios, methods guide, official directory,
  discovery-site exclusions and route-approach flags. These are reported completed
  in the latest project notes; this planning pass did not rerun analytical validation.
- September 8 STATUS reports seven Python tests and 11,436 scenario checks plus
  browser checks passing. Treat as prior evidence, not a fresh test result.
- Earlier releases are recorded as deployed; the latest Contra Costa work is recorded
  as uncommitted and unpublished. Live content was not audited in this planning pass.
- Other source branches: `master` (LA), `san-ramon`, `bakersfield`. Do not assume
  they have Contra Costa's schema, source quality, UI or defaults.
- `deploy.sh` archives committed city branches, then force-pushes a generated
  `gh-pages`. It currently omits `data/cooling_directory_contracosta.json`.
  Running it now would not publish the dirty working tree.
- Current documentation is mixed with older claims: README and historical feature
  sections describe older ACS/canopy/walking behavior. Current summaries need to be
  unambiguous without deleting the audit trail.

## Release scope

Recommended next publication: a transparent public analytical explorer, with
Contra Costa as the current reference implementation and explicitly described
legacy city versions. Preserve existing URLs. Keep planting outputs conditional,
walking tied to its documented discovery inventory, and official contacts separate.

Operational municipal planning and an emergency/open-now route service are later
acceptance levels. Do not make publication depend on developing a novel surface-
temperature intervention model. Do not add AI/chat, accounts or a new framework
unless a specific user workflow requires them.

## Work queue to publication

Each row is a work packet. Complete dependencies first and record evidence in
HANDOFF.md. Owners are preferences, never requirements.

| ID | Work and acceptance | Primary / backup | Depends |
|---|---|---|---|
| CE-01 | Establish baseline: inspect all existing diffs/untracked files, preserve pre-rebuild comparison data, run existing Python/JS suites, record branch/head, exact results and unresolved changes. Create a reviewed checkpoint without sweeping unknown files into it. | Opus / Astra | None |
| CE-02 | Reconcile current docs: one current city/version matrix; sources, years, population allocation, canopy coverage, modeled A/C, route denominator and assumptions agree across README, FEATURES, DATA_QUALITY, guide, findings and pitch. Label superseded audit notes explicitly. Remove unsupported current headline claims; retain limitations. | Sonnet / Opus | CE-01 |
| CE-03 | Targeted analytical release review: inspect canopy area/coverage/missingness, occupied-home weighting, census reconciliation, score parity and ties, default weights, scenario bounds and route flags. Recompute affected evidence only if defects require it. Validate sampled outputs against source inputs, and trace public claims to evidence. | Fable / Astra or Opus | CE-01 |
| CE-04 | Close claim gaps: keep directory and OSM discovery service sets distinct; expose checked date, source, contact guidance, missing hours/eligibility and routing limitations. Ensure marker filters do not imply recomputed service access. Verify current official source before release. | Opus / Astra | CE-02, CE-03 |
| CE-05 | UI release pass: freeze an approved desktop/mobile visual reference; finish panel/map layout, readable legends, selected-cell details, methods and directory navigation. Verify keyboard/focus, contrast, touch behavior, units, reset/presets and narrow-screen layout in browser. Implement against the reference, not a fresh redesign each session. | Astra direction, Opus implementation / Fable | CE-02, CE-04 |
| CE-06 | Reproducible scenario export: JSON/CSV containing cell IDs, city, dataset hash/version, weights, planting share and constants, source/coverage flags and interpretation. Round-trip reload reproduces results and rejects incompatible versions visibly. Recommended before planner sharing; may be deferred for an explicitly exploration-only release. | Opus / Sonnet with specification | CE-03, CE-05 |
| CE-07 | Build and deployment repair: include directory JSON and all required local assets; add build-only output and release manifest identifying source commits/data hashes; fail on missing required files and unexpected branch state. Test the assembled site at all four city prefixes, including guide/directory fetches. Record the previous deployed commit and a rollback procedure. No automatic production push in a test. | Opus / Astra | CE-01, CE-04 |
| CE-08 | Release QA on the assembled artifact: existing suites, startup/schema failures, empty/unknown data, optional-site failure, basemap outage/flat mode, slow loading, console/network errors, mobile and desktop browsers, external-data text rendering, local dependencies and attribution. Confirm changes are limited to intended city branches. | Sonnet execution, Opus fixes / Astra | CE-05, CE-07; CE-06 if included |
| CE-09 | Release content: align chooser, methods, README, demo/deck and findings to shipped city versions. Explain exploratory scope, source dates, known limitations and feedback contact. Remove any statistical headline still dependent on invalid aggregation; do not invent replacement significance. | Sonnet / Opus | CE-02, CE-03, CE-08 |
| CE-10 | Publish reviewed source commits through repaired build, verify live routes/assets/data versions and one real user flow per city, record release and rollback hashes, refresh ownership/cadence, and update STATUS. Publication requires the user's release instruction; this plan alone is not an instruction to push. | Opus / Astra | CE-08, CE-09 |

CE-03 is a bounded correctness audit, not an instruction to rerun every satellite
download or solve all research questions. Source refreshes must preserve actual
before-state data so rebuild reports do not compare against an invented baseline.

## Work after an explorer release, before stronger operational claims

1. Verify official facilities' coordinates/entrances, hours, eligibility, accessibility
   and update responsibility. Route against that service set and assess approach
   barriers/disconnected paths; test closure/filter behavior explicitly.
2. Validate canopy against independent local samples, investigate rural/fringe and
   legacy coverage, validate demographic allocation, and propagate uncertainty
   into rank stability. Compute income-equity findings at defensible native geography.
3. Obtain local planting/cost/species/growth/survival evidence and review by relevant
   city staff. Confirm actual plantability before describing implementable sites.
4. Pilot with city users, document support/refresh ownership and accessibility
   acceptance. A locally validated cooling/comfort model is separate research scope.

These are meaningful work packages, but some need external evidence or people;
neither provider can complete those dependencies simply by writing more code.

## Switching providers without rebuilding context

- Use the same repository and branch sequentially. Stop the outgoing writer before
  starting the incoming one. Two agents editing app/index.html or generated data
  concurrently is likely to cost more than it saves.
- Parallel work requires separate worktrees and explicit file ownership. Avoid
  cherry-picking entire city-specific implementations across incompatible branches.
- At each completed packet or meaningful partial checkpoint, update HANDOFF.md:
  active ID, intent, files/branches changed, exact commands and outcomes, incomplete
  edits/processes, decisions, and the next concrete action. Do not wait for a cap.
- Keep one implementation owner. Ask the second model to review a specific diff or
  invariant at milestones, not to reread and redesign the entire project each time.
- Preserve approved screenshots and design decisions with the task evidence so
  Claude can continue UI work if Astra is unavailable.
- At a hard interruption, incoming agent reads git diff/status and HANDOFF before
  modifying anything. Files are the recovery source; conversational memory is optional.
- Fallbacks: Astra unavailable → Opus implements, Fable reviews hard issues; Fable
  capped → Opus continues; all Claude capped → Astra takes the next packet. A bounded
  task with exact acceptance checks can also move from Opus to Sonnet.

## Portable start/resume prompt

> Continue Cool Equity in this checkout. Read AGENTS.md, DELIVERY_PLAN.md and
> HANDOFF.md, then the current (not superseded) sections of PRODUCT_READINESS.md,
> FEATURES.md and DATA_QUALITY.md. Inspect branch, HEAD, git status and relevant
> diffs before editing; preserve pre-existing uncommitted and untracked work.
> Take the active packet, or the next dependency-ready packet. Complete its
> acceptance checks and record actual results. Work only on the declared city
> branches; preserve scientific limitations and source distinctions. Update
> FEATURES.md and DATA_QUALITY.md with any product/data changes and STATUS.md for
> significant work. At each meaningful checkpoint update HANDOFF.md with changed
> files, checks, unresolved issues and the exact next action. Do not restart the
> project, redo completed analysis without cause, or publish unless requested.

First Claude assignment: CE-01, then CE-07's build-only deployment repair. The
directory packaging omission is a concrete, bounded engineering task and an
efficient way to establish the handoff workflow before more expensive review.
