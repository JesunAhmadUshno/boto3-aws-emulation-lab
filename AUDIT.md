# Audit: boto3 AWS Emulation Lab

Self-audit against the standing project standard, written after
the generated results and before this file was committed. Verdicts
were published either way, including the refuted one.

## Headline claim check (Jev)

The headline verdicts (24 of 30 MATCHES, H1 CONFIRMED, H2
REFUTED, H3 CONFIRMED, the per-service counts and the six named
non-MATCHES rows) were screened with the house claim_check gate
(TypeSafe Jev, model jev-1.13.0, one noul question "supported").
Jev returned noul 0.31, which is the REVIEW band (clear at 0.85,
block at 0.10), so every figure was verified by hand against
results/summary.json and results/scores.json before anything was
published, and all figures agree. The screen, its route and the
hand verification are recorded in results/jev-claim-check.json.

## What was verified by hand

- The pre-registration is the root commit (2b2659d) and predates
  the harness and every run; BEHAVIOURS.md was committed before
  the harness (28bfcf2 before d9d1913).
- Every number in README.md and RESULTS.md traces to
  results/scores.json through scripts/make_results.py. The counts
  were recomputed from the raw records during the Jev hand
  verification and agree.
- The three run-1 ERROR rows were root-caused by probes before
  any fix (DECISIONS.md D5), and only the four affected rows were
  rescored, through scripts/rerun_rows.py; the other 26 records
  are the original run's, untouched.
- No real AWS was touched: the factory forces 127.0.0.1, the guard
  test fails on any other endpoint, the credentials in code are
  obvious placeholder strings, and instance metadata is disabled
  in the harness process.
- Docker is absent on the machine of record (verified, DECISIONS.md
  D1), so no LocalStack arm exists and nothing in the build depends
  on it.

## Grade: 5,600 of 10,000

Itemized deductions. Nothing is rounded up.

- **-1,200: the Lambda execution rows are environment-bound, not
  semantic.** L-02 and L-03 are UNSUPPORTED because this machine
  has no Docker, not because moto's invocation semantics were
  measured and found wrong. On a Docker host those rows might
  match, diverge, or fail differently, and this study cannot say
  which. Two of the seven Lambda rows therefore carry less
  information than the design intended.
- **-700: one emulator only.** The LocalStack arm was dropped
  (D1), so every claim in this study is a claim about moto 5.2.5,
  while the research question says "a local emulator". The README
  names moto throughout, but the comparison the question gestures
  at was never run.
- **-600: one pass per row.** Each row was executed once in the
  scored run (plus the registered subset reruns). The
  timing-sensitive rows (Q-02, Q-04, Q-05, F-01) rest on single
  passes with wide margins, not on repetition statistics, so
  flakiness in either direction would not have been detected.
- **-500: the H2 refutation leans on kind SQS coverage.** All 10
  SQS rows matched, but the frozen list omits SQS areas where
  emulators commonly stray: delay queues, message retention,
  batch APIs, and ordering across multiple FIFO groups. H2 is
  REFUTED as frozen; a harder list might have confirmed it.
- **-500: the presigned-URL divergence is only half isolated.**
  S3-09 measures boto3's default signing against a custom
  endpoint. The s3v4-configured variant, which would separate
  "SDK default" from "emulator behaviour" completely, was not
  measured.
- **-400: S3 Select coverage is one query and one format.** A
  single CAST comparison over CSV. JSON input, LIKE predicates
  and aggregate functions are unmeasured, so the UNSUPPORTED
  verdict bounds the documented subset narrowly.
- **-300: the attribute MD5 oracle lacks an independent vector.**
  The documented algorithm in src/oracles.py was checked against
  the emulator, not against a worked example published by AWS,
  so a shared misreading of the document by oracle and author
  would pass silently. (Name-order invariance and change
  sensitivity are unit-tested; the algorithm text is cited.)
- **-200: one assertion demoted to a note.** S3-05 records the
  HTTP status of the deleted-version read as a note rather than
  an assertion, because the frozen expectation named only the
  error code. The record is complete, but the scoring surface is
  one assertion thinner than its neighbours.

## Left undone, with reasons

- LocalStack arm: impossible on this machine (no Docker, D1).
- Lambda execution semantics: blocked by the same absence; the
  rows are scored UNSUPPORTED with the emulator's error quoted,
  which is the honest result for this machine of record.
- A repetition study for the timing rows: outside the frozen
  design; noted above as a deduction instead of quietly added.

Nothing was published outside this GitHub repository. No real
AWS account, credential or endpoint was used. No spend.
