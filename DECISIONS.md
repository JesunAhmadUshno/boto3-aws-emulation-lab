# Decisions

Decisions taken during the build, in the programme's house form.
Anything that changes how a run is executed is recorded here, before
the runs it affects, with its reason.

## D5: Classification fixes after scored run 1 (S3-09, S3-12, L-02, L-03)

The first scored run (2026-11-08) left three rows as ERROR and one
row under-characterized. Each cause was established by a probe
before any fix, and only the affected rows are rescored, per
PREREGISTRATION.md Section 7. No expectation in BEHAVIOURS.md
changes.

- L-02 and L-03 (invoke): moto returns HTTP 200 with a payload that
  is plain text, "error running docker: Error while fetching server
  API version ... FileNotFoundError", because moto executes Lambda
  zip functions through Docker and this machine has none (D1). The
  functions never execute. The rows now detect that emulator error
  text in the payload and score UNSUPPORTED with it quoted, which
  is the outcome the pre-registration predicted for whatever moto
  cannot execute.
- S3-12 (S3 Select): the server answers the documented CAST query
  with HTTP 500. An in-process probe shows why: moto's SQL parser
  (py_partiql_parser) raises ValueError on the CAST where-clause.
  The row now scores that refusal UNSUPPORTED with the error
  quoted, instead of letting it escape as a harness ERROR.
- S3-09 (presigned URL): scored DIVERGES in run 1 and stays
  DIVERGES. The diff is now characterized in the record: boto3
  signs presigned URLs for a custom endpoint with Signature
  Version 2 style parameters (AWSAccessKeyId, Signature, Expires
  as an epoch), not the SigV4 X-Amz parameters of the AWS
  document, while the unsigned fetch of the URL returns the exact
  object bytes. The row gains a note recording the observed
  parameter names; no assertion changes.

## D4: Subset reruns merge into results/scores.json

scripts/rerun_rows.py runs named rows against a fresh server and
replaces only their records in results/scores.json. Rows use unique
resource names and a fresh server per run, so a subset rerun is the
same measurement as the same rows in a full run, and untouched rows
keep their original records byte for byte.

## D3: The Lambda execution role is created inside the emulator first

Recorded after harness validation and before the scored run. The
frozen behaviour file passes a placeholder role ARN pattern and
notes that an emulator validating role existence is scored on that.
Validation finding: moto 5.2.5 does validate. Creating a function
with the literal placeholder ARN fails with
InvalidParameterValueException, "The role defined for the function
cannot be assumed by Lambda", which is also the documented AWS
behaviour for a role that cannot be assumed, so on this point the
emulator matches the service. Keeping the literal placeholder would
collapse every Lambda row into that one setup fact and measure
nothing about Lambda itself. The harness therefore creates the
execution role through moto's IAM first (the documented setup step
for CreateFunction) and passes the returned ARN to the Lambda rows.
The placeholder string is never a working credential; it remains in
src/factory.py only as the Context default and as an honesty marker.
IAM itself is setup machinery and is not a scored service.

## D1: No LocalStack arm; moto is the only emulator under test

Recorded before the pre-registration was locked. The brief allowed a
LocalStack arm only if Docker first verifiably works on this
machine. It does not: `docker` is not installed on htch-runtime
(`docker: command not found`, verified 2026-11-08), and installing a
container runtime system-wide on a shared machine is a heavier change
than this study needs. The study therefore tests moto alone, which
is also the emulator named first in the research question. Nothing
in the frozen design depends on Docker; the Lambda execution rows
are precisely where its absence is expected to become evidence, and
the scoring rules already have a vocabulary for that outcome
(UNSUPPORTED, with the emulator's error quoted).

## D2: moto runs in server mode, not in-process

The harness starts moto's ThreadedMotoServer on 127.0.0.1 with an
ephemeral port and points every boto3 client at it through the
client factory. In-process mocking was rejected for two reasons:
the presigned-URL row (S3-09) requires a real HTTP fetch of a signed
URL, which only a listening server can answer; and HTTP-level
behaviour (status codes, error documents) is part of the scored
surface, so the study goes through real HTTP on loopback rather
than through botocore's transport interception. No connection ever
leaves the loopback interface: the guard test in tests/ asserts the
endpoint host of every client the factory creates.

## D6: Portfolio standard v2 adopted (2026-11-08, after the results)

Recorded after the results; changes no row, expectation or verdict.

- The README opens with the standard's abstract, lifecycle and a
  layout table. Locked file names stay: PREREGISTRATION.md is the
  proposal, AUDIT.md the report, RESULTS.md the results, this file
  the decisions, results/scores.json and results/versions.json the
  raw evidence.
- The lock is the root commit 2b2659d (tag proposal-v1).
  tests/test_layout.py pins the SHA-256 of PREREGISTRATION.md as
  committed there and of BEHAVIOURS.md as committed in 28bfcf2.
- AUDIT.md's grade section left the public repo (grades are
  internal). Its itemized limits stay in AUDIT.md as threats to
  validity, without point values.
- Two record-keeping gaps found while adopting the standard, kept
  as found rather than edited into the evidence: D5 and
  scripts/rerun_rows.py cite "PREREGISTRATION.md Section 7" for the
  rerun policy, which is Section 5; and Section 5 asks that a rerun
  be noted on the row, which the S3-09 and S3-12 records do (their
  notes cite D5) but the L-02 and L-03 records do not. D5 is the
  note for all four rows.
- Field profile declared: Systems and infrastructure, reliability.
  The study does not meet that profile's items (no recovery targets,
  drills, monitoring or runbook), so the verdict is Functional.

## D7: Review fixes (2026-11-08, after the results)

Recorded after an independent review; changes no row, expectation or
verdict.

- The README headline now says the run was on a host without Docker
  and that L-02 and L-03 are UNSUPPORTED for that reason. The
  reviewer reported that a rerun on a Docker host scored both
  MATCHES (26 of 30). That is a separate, unscored measurement on
  another machine; the scored record stays the htch-runtime run.
- The run-1 records for S3-09, S3-12, L-02 and L-03 were never
  committed (results/ first appears in 624027e, after the reruns), so
  they cannot be restored. scripts/make_results.py now adds the rerun
  note Section 5 asks for to all four rows in RESULTS.md, with each
  row's run-1 status (S3-09 DIVERGES, the others ERROR, per D5),
  leaving results/scores.json as recorded.
- scripts/rerun_rows.py now appends every record it replaces, dated,
  to results/replaced-records.json and adds a "rerun:" note to the new
  record, so a future rerun cannot overwrite evidence. Its docstring
  now cites Section 5, the correct section (D6).

## D8: Gap-closure rerun of the Lambda rows on a Docker host (registered 2026-11-18, before the run)

Rows L-02 and L-03 scored UNSUPPORTED in the committed run because moto
5.2.5 executes Lambda invocations in a container and no Docker host was
available on the machines the study ran on. This amendment registers a
rerun of rows L-02 and L-03, plus a full-suite cross-check (all 30
rows), on the Dell PowerEdge R610 (Ubuntu 24.04, Docker 29.1.3, Python
3.12.3), under the gap-closure orders of 2026-11-17 and 2026-11-18.

Machine history, stated once so the copies do not diverge silently: the
rerun was first planned on BlackBoxV2 and registered there as D6 in
that working copy; when BlackBoxV2 became unreachable it was
re-registered on BlackBoxV3 in a main-tarball copy (also as that copy
next entry); neither machine could run it (V2 offline, V3 has no
container runtime). It is executed here. Same plan, no content change.

Plan. The Lambda runtime image moto requests
(ghcr.io/shogo82148/lambda-python:3.12) is pulled before any scoring
and the pull is confirmed complete. Rows run through the repo own
scripts (scripts/rerun_rows.py L-02 L-03, then scripts/run_study.py for
the full suite) in a venv built from requirements.txt (boto3/botocore
1.43.126, moto[server] 5.2.5, pytest 9.2.0). Frozen protection:
results/scores.json is snapshotted before the runs; the fresh records
are written to new files (results/r610_2026-11-18_lambda_rows.json and
results/r610_2026-11-18_full_suite.json) and the committed scores.json
is restored byte-identical afterwards. Fresh verdicts are reported
beside the committed ones in the outcome entry; the run itself edits no
committed verdict.

D8 addendum (2026-11-18, before the run): the fresh clone requirements.txt
carries a post-study dependabot bump (bb490a7) to boto3/botocore 1.44.2.
The rerun installs the environment of record explicitly
(boto3==1.43.126, botocore==1.43.126, moto[server]==5.2.5,
pytest==9.2.0), so the fresh verdicts are comparable to the committed
ones; the clone requirements.txt itself is not edited. Host Python is
3.12.3; the venv was bootstrapped with get-pip.py because the host has
no ensurepip (python3.12-venv absent), which changes nothing about the
environment inside the venv.

D8 outcome (2026-11-18): executed on the R610 as registered. The Lambda
runtime image (ghcr.io/shogo82148/lambda-python:3.12, 1.2 GB) was
pulled and confirmed before scoring. Environment: Python 3.12.3,
boto3/botocore 1.43.126, moto 5.2.5, pytest 9.2.0 (repo tests 16
passed). Rows L-02 and L-03, rerun through scripts/rerun_rows.py on the
Docker host, both score MATCHES (fresh records:
results/r610_2026-11-18_lambda_rows.json). The full-suite cross-check
(scripts/run_study.py, fresh records:
results/r610_2026-11-18_full_suite.json) scores 26 MATCHES / 3
DIVERGES / 1 UNSUPPORTED against the committed 24 / 3 / 3, and the
only rows that move are L-02 and L-03 (UNSUPPORTED to MATCHES); every
other row, including S3-12 (UNSUPPORTED for a non-Docker reason),
reproduces its committed verdict exactly. The committed
results/scores.json was restored byte-identical after the runs (md5
eb8bbfcfa5e20c61ebead580059e1be2). Reading: the two Lambda invocation
behaviours were never departures from the documented boto3 behaviour;
they were unmeasurable without a container runtime, and on one they
match. Any restatement in RESULTS.md or the paper is a separate,
labelled decision.
