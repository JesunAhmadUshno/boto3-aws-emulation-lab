# Pre-registration: boto3 AWS Emulation Lab

Locked before any measured run exists. The commit that adds this file is
the first content commit in this repository and precedes every harness
file and every result; git history proves the order. Any change to this
file after locking is an amendment and must be recorded in DECISIONS.md
with its reason, before the runs it affects.

## 1. Research question

How far can boto3 evidence gathered against a local emulator be
trusted? Across the S3, SQS and Lambda patterns a working engineer
actually uses, which documented behaviours does the emulator reproduce
exactly, which does it diverge on, and which does it not support at
all?

Documentation states the behaviours. This study scores them, one by
one, against the emulator, and publishes the divergence list either
way.

## 2. Absolute scope rule

Emulation only. There is no real AWS account in this study, no real
AWS credential, and no network call to any AWS endpoint. Every boto3
client is created by one factory in the harness that forces
`endpoint_url` to a moto server bound to 127.0.0.1 on an ephemeral
port. A guard test asserts that every client the harness creates has
a 127.0.0.1 endpoint host; the study does not run if the guard fails.
Credentials are dummy placeholders defined in the harness code
(obviously fake strings), passed to boto3 explicitly at client
creation inside the test process only. No credential of any kind is
read from the environment, from a file, or from instance metadata
(the harness sets AWS_EC2_METADATA_DISABLED=true and constructs its
own boto3 session).

## 3. Environment (frozen)

Machine of record: this VM, hostname htch-runtime, Linux
7.0.0-43-generic x86_64, Python 3.12.3.

Pinned client surface (the pins are part of the result):

- boto3 1.43.126
- botocore 1.43.126
- moto 5.2.5 (server mode, ThreadedMotoServer, one fresh server per
  full scored run, bound to 127.0.0.1, ephemeral port)
- pytest 9.2.0 (unit and semantic tests only; the scored run is
  driven by scripts/run_study.py)
- requests 2.34.2 (used for the unauthenticated presigned-URL fetch)

Region is us-east-1 throughout. The moto account id is the emulator
default. Docker is not used: no Docker binary exists on this machine
(verified 2026-11-08 before this lock; see DECISIONS.md D1), so the
LocalStack arm considered in the brief is not run, and the study does
not depend on a container runtime.

## 4. Behaviour list and expectations

The frozen behaviour list, with the documented expectation for each
behaviour written from AWS's own documentation before any test runs,
lives in BEHAVIOURS.md. It is committed immediately after this lock
and before any harness code exists. No expectation in BEHAVIOURS.md
may be edited after the scored run begins. A correction is recorded
in DECISIONS.md, and the affected behaviour is rescored as a new row
whose id carries the suffix "b"; the original row keeps its recorded
outcome, and the "b" row is reported alongside it but excluded from
the hypothesis arithmetic in Section 6, with the discrepancy
explained in RESULTS.md.

The list holds 30 scored rows: 12 S3, 9 SQS, 7 Lambda, and 2 failure
study rows (F-01 SQS redrive under a consumer that never deletes,
F-02 racing writers on a versioned S3 bucket), each scored against
the same documents as its parent behaviour.

## 5. Scoring rules (frozen)

Each row produces assertions derived mechanically from its frozen
expectation. The row scores:

- MATCHES: every assertion holds against the emulator.
- DIVERGES: the operation completes (or fails with an error) but at
  least one assertion differs from the documented expectation. The
  observed value and the expected value are both recorded.
- UNSUPPORTED: the emulator refuses the operation as not implemented
  or unsupported, or the API surface needed does not exist in the
  emulator. The emulator's error is quoted verbatim in the record.

A harness defect (a bug in this repository's own test code, as
opposed to emulator behaviour) is fixed, recorded in DECISIONS.md,
and only the affected rows are rerun; the rerun is noted on the row.
Timing-sensitive rows use the frozen waits of BEHAVIOURS.md and a
single repetition; a timing row that fails on a boundary is rescored
once and both attempts are recorded.

## 6. Hypotheses (frozen, with numeric lines)

- H1: at least 70 percent of the 30 frozen rows score MATCHES.
  Below 70 percent, H1 is REFUTED. Exactly at the line counts as
  CONFIRMED (the line is "at least").
- H2: each of the three services (S3, SQS, Lambda) has at least one
  row scoring DIVERGES or UNSUPPORTED. All three services showing
  such a row confirms H2; any service with none refutes it.
- H3: the two queue semantics most relied on in production both
  score MATCHES exactly: Q-02 (visibility timeout hides, then
  reveals, an undeleted message) and Q-04 (dead-letter redrive
  after maxReceiveCount). Either one scoring anything else refutes
  H3.

Verdict language is CONFIRMED, REFUTED, or INCONCLUSIVE (the last
only if a row cannot be executed at all for a harness-side reason
that survives the rerun policy, which would also be reported).

## 7. Failure study (frozen)

- F-01: a consumer that receives and never deletes, on a queue with
  VisibilityTimeout 1 second and a redrive policy with
  maxReceiveCount 3 targeting a dead-letter queue. Documented
  expectation: the message is received 3 times, then moved to the
  dead-letter queue; the source queue stops returning it; the
  dead-letter queue returns the original body.
- F-02: two writers put different bodies to the same key of a
  versioning-enabled bucket, then an unversioned delete is issued.
  Documented expectation: both versions persist and are individually
  readable by version id; the unversioned delete adds a delete
  marker; a plain GET then fails with HTTP 404; deleting the delete
  marker by its version id makes the second body readable by plain
  GET again.

## 8. What is not claimed

Nothing in this study measures real AWS. A MATCHES row means the
emulator reproduced the documented behaviour on this run, on these
pins; it is evidence about the emulator, transferable to real AWS
only through the document both were scored against. Latency and
throughput are not measured: an emulator's timing says nothing
about the service, and this study refuses to publish numbers that
would pretend otherwise.
