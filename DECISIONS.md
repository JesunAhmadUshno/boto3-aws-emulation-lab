# Decisions

Decisions taken during the build, in the programme's house form.
Anything that changes how a run is executed is recorded here, before
the runs it affects, with its reason.

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
