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
