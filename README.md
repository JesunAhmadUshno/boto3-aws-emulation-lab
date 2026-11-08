# boto3 AWS Emulation Lab

This is an emulation study: every measurement was taken against a local moto server on one machine, and no real AWS account, credential or network endpoint was touched at any point.

## Research question

How far can boto3 evidence gathered against a local emulator be
trusted? Across the S3, SQS and Lambda patterns a working engineer
actually uses, which documented behaviours does the emulator
reproduce exactly (MATCHES), which does it diverge on (DIVERGES),
and which does it not support at all (UNSUPPORTED)?

The design was frozen before any run: PREREGISTRATION.md (the root
commit of this repository) fixes the pins (boto3 1.43.126, moto
5.2.5), the machine of record (htch-runtime), the scoring rules and
three hypotheses. BEHAVIOURS.md freezes the 30 scored behaviours,
each with its expected result written from AWS's own documentation
and its document cited. RESULTS.md is generated from the recorded
run by scripts/make_results.py; nothing in it is hand-typed.

## Verdicts

- **H1 CONFIRMED.** At least 70 percent of the frozen rows score
  MATCHES: 24 of 30 rows matched (80.0 percent).
- **H2 REFUTED.** The hypothesis was at least one DIVERGES or
  UNSUPPORTED row per service. S3 and Lambda each have them; SQS
  has none. All 10 frozen SQS rows, including visibility timeout,
  dead-letter redrive and the never-delete failure study, matched
  the documents exactly.
- **H3 CONFIRMED.** The two queue semantics production code relies
  on most, visibility timeout (Q-02) and dead-letter redrive
  (Q-04), both score MATCHES exactly.

Counts: S3 10 MATCHES, 2 DIVERGES, 1 UNSUPPORTED of 13 rows.
SQS 10 MATCHES of 10 rows. Lambda 4 MATCHES, 1 DIVERGES,
2 UNSUPPORTED of 7 rows. Total 24 MATCHES, 3 DIVERGES,
3 UNSUPPORTED of 30.

## Where the emulator departs from the documents

The divergences and unsupported behaviours are the primary
deliverable. Each is stated with its evidence in RESULTS.md.

Diverges (it runs, but not as documented):

- **S3-09, presigned URL shape.** boto3 signs presigned URLs for a
  custom endpoint with Signature Version 2 style parameters
  (AWSAccessKeyId, Signature, Expires as an epoch), not the SigV4
  X-Amz parameters the AWS document describes. The unsigned fetch
  of the URL returns the exact object bytes, so the URL works; its
  shape is not the documented one. A test that asserts the
  documented shape against an emulator endpoint fails for a reason
  that has nothing to do with the emulator's S3.
- **S3-10, Content-MD5 not verified.** A put with a deliberately
  wrong Content-MD5 is accepted and the object is stored. Real S3
  rejects it with BadDigest and stores nothing. An upload-integrity
  test that passes against moto proves nothing about this check.
- **L-05, invalid runtime accepted.** CreateFunction with the
  runtime string "python2.7-removed-runtime" succeeds. Real Lambda
  rejects an unsupported runtime with
  InvalidParameterValueException. Validation tests against moto
  cannot see this rejection.

Unsupported (the emulator cannot do it here; errors quoted in
RESULTS.md):

- **L-02 and L-03, function execution.** moto executes Lambda zip
  functions through Docker. This machine has no Docker
  (DECISIONS.md D1), so Invoke returns HTTP 200 with the emulator's
  own "error running docker" text as the payload and the function
  never runs. Synchronous invocation, the behaviour engineers test
  most, is exactly the behaviour this setup cannot evidence.
- **S3-12, S3 Select.** The documented SELECT with a CAST
  comparison is answered with HTTP 500; moto's SQL parser raises
  ValueError on the CAST where-clause (probe evidence in
  DECISIONS.md D5).

What matched is equally load-bearing: byte-exact object round
trips, versioning state transitions including delete markers,
tagging, pagination, range reads, every frozen SQS behaviour
including FIFO deduplication and group order, the documented MD5
of message attributes, and Lambda's create, describe, concurrency
and delete surface. One setup finding is recorded in DECISIONS.md
D3: moto validates that the Lambda execution role exists, with the
same error AWS gives, so the role is created inside the emulator
first, as the documents prescribe.

## Why this matters beyond this repository

Small teams test against emulators because cloud bills are real:
nobody sane pays AWS rates to find out whether a queue redrives
correctly. But an emulator is a claim about a service, made by
people who did not build the service, and the claim is uneven.
This study measured exactly where one widely used emulator's
claim holds (all of the frozen SQS surface, most of S3) and where
it silently does not (an integrity check that is not performed, a
validation that is not applied, an execution path that needs a
container runtime the test machine may not have). Knowing which
is which is the difference between a test suite and a
superstition: the suite tells you what your code does; the
superstition tells you what you hoped.

## Reproduce

```sh
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest tests/ -q      # guard, scoring, smoke (fast)
.venv/bin/python scripts/run_study.py     # the scored run: fresh server, 30 rows
.venv/bin/python scripts/make_results.py  # RESULTS.md and results/summary.json
```

The scored run takes about half a minute (several rows wait out
real visibility timeouts). Every client is built by
src/factory.py, which forces the endpoint to 127.0.0.1 and uses
obviously fake placeholder strings as the signing credentials
inside the test process only; tests/test_guard.py fails if a
client ever points anywhere else.

## Layout

- `PREREGISTRATION.md`: frozen design, hypotheses, scoring rules.
- `BEHAVIOURS.md`: the 30 frozen behaviours with cited documents.
- `RESULTS.md`: generated verdicts and the full scored table.
- `AUDIT.md`: honest self-audit, graded out of 10,000.
- `DECISIONS.md`: D1 to D5, including the dropped LocalStack arm
  and the post-run classification fixes.
- `src/`: client factory and guard, row implementations, runner.
- `scripts/`: the scored run, subset reruns, results generator.
- `results/`: raw per-row records (scores.json), versions,
  summary, and the Jev claim check.

Licence: Apache-2.0 (LICENSE). Component provenance: LICENSES.md.
