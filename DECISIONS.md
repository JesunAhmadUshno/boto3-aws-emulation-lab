# Decisions

Decisions taken during the build, in the programme's house form.
Anything that changes how a run is executed is recorded here, before
the runs it affects, with its reason.

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
