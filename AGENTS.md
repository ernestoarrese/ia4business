# Gate0 — Agent Working Protocol

Gate0 Packaging QA is a functional MVP for packaging prepress review and Production Readiness.

Agents must prioritize stability, traceability, and small safe changes.

## Product position

Gate0 is not an automatic prepress replacement.

Gate0 is a Production Readiness assistant for flexible packaging files. It helps prepress teams upload and analyze PDF files, detect technical and operational risks, prioritize review, inspect evidence when available, support GO / HOLD / REVIEW decisions, and compare artwork candidates when applicable.

## Critical files

Treat these files as sensitive:

- gate0_check.py
- business_rules.py
- readiness_engine.py
- readiness_summary.py
- check_intelligence.py
- config/spot_utils.py
- dashboard/index.html
- gate0_orchestrator.py
- app.py
- gate0/services/*

## Mandatory workflow

Before changing code, run:

- git status --short
- git log --oneline -8
- pytest -q

After changing code, run:

- python -m py_compile app.py gate0_check.py gate0_orchestrator.py business_rules.py readiness_engine.py readiness_summary.py check_intelligence.py config/spot_utils.py
- pytest -q
- git status --short
- git diff --stat

If dashboard/index.html changes, also run node --check on the extracted dashboard JavaScript.

## Commit rules

Use small commits.

Preferred commit types:

- test:
- fix:
- refactor:
- ux:
- product:
- docs:
- chore:

## What agents must not do

Do not:

- perform broad refactors without explicit request;
- change business thresholds without tests and explanation;
- change Production Readiness behavior without guardrail tests;
- modify dashboard JavaScript without node --check;
- remove legacy-looking code unless tests prove it is obsolete;
- touch real customer files or add them to git;
- commit generated runtime files from data/runtime;
- commit local backup bundles;
- change severity semantics casually;
- convert contextual INFO findings into blocking risks without product decision;
- claim Gate0 can automatically correct prepress files.

## Business rule safety

Any change to business_rules.py must preserve or intentionally update tests for RGB object behavior, High TAC behavior, font embedding behavior, low image resolution, small text, spot/separation rules, readiness scoring, and contextual/non-blocking behavior.

## Production Readiness safety

Any change to readiness_summary.py or readiness_engine.py must preserve or intentionally update tests for active PR2 version, outside confirmed printable area downgrade, unconfirmed printable area not downgraded, white overprint priority, small text deduplication, and GO / HOLD / REVIEW behavior.

## Dashboard safety

Any change to dashboard/index.html must preserve:

- Production Readiness block;
- Riesgos principales;
- Detalle del riesgo;
- PR2 drilldown;
- risk preview;
- visual zone / occurrence navigation;
- separation usage inline markers;
- PDF viewer.

## Runtime safety

Do not regress session isolation.

The web runtime must use session-specific files under data/runtime, not shared global report files for active web analysis.

Legacy data/output may remain only as CLI/fallback behavior.

## Compare Engine safety

For Compare Engine work:

- audit before modifying;
- preserve existing tests;
- add tests before UX changes;
- separate executive comparison result from low-level comparison details;
- do not overclaim visual equivalence unless supported by actual comparison logic.

## First Codex task

The first Codex task on this repo should be audit-only.

Codex should not modify files until it has inspected repo state, identified relevant files, summarized risks, proposed a small plan, and waited for explicit approval.
