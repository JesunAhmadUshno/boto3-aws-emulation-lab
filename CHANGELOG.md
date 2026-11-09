# Changelog

All notable changes to this project. Format: Keep a Changelog 1.1.
Versions follow Semantic Versioning; no release is tagged yet.

## [Unreleased]

### Changed
- 2026-11-08: Review fixes (DECISIONS.md D7). README headline names
  the Docker-less host and the two Lambda rows it makes UNSUPPORTED.
  RESULTS.md notes the rerun on the four rescored rows (generator
  change). scripts/rerun_rows.py keeps replaced records in
  results/replaced-records.json and notes each rerun on the row.
- 2026-11-08: Adopted the portfolio standard v2. README opens with the
  question, headline, field, job family and verdict (Functional),
  then reproduce, lifecycle and layout. AUDIT.md is the report; its
  grade moved out of the public repo (grades are internal) and its
  limits stay as threats to validity, with a new "How the evidence
  is protected" section. DECISIONS.md D6 records the adoption. A test
  fails if PREREGISTRATION.md or BEHAVIOURS.md changes by one byte.
  CI runs with read-only permissions and checks that RESULTS.md and
  results/summary.json regenerate unchanged. CodeQL, Dependabot,
  CITATION.cff and SECURITY.md added.

### Added
- 2026-11-08: Scored run of all 30 frozen rows on moto 5.2.5,
  generated RESULTS.md, AUDIT.md, claim check (624027e).
- 2026-11-08: Harness: client factory with loopback guard, 30 row
  implementations, results generator, tests, CI (d9d1913).
- 2026-11-08: Frozen behaviour list, decisions D1 and D2 (28bfcf2).
- 2026-11-08: Pre-registration (2b2659d), before any code or run.
