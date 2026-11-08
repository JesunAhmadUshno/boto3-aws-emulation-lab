# Frozen behaviour list

Committed immediately after PREREGISTRATION.md and before any harness
code exists. Each row states the documented expectation, written from
AWS's own documentation (cited per row), before its test runs. No row
may be edited after the scored run begins; corrections follow the
rescoring rule in PREREGISTRATION.md Section 4.

Scoring vocabulary: MATCHES (every assertion holds), DIVERGES (the
operation runs but an assertion differs; expected and observed are
both recorded), UNSUPPORTED (the emulator refuses the operation as
not implemented or the API surface is absent; the error is quoted).

## S3

### S3-01: Put and get round-trip is byte exact
Put a 1,024-byte binary body, then get it. Expectation: HTTP 200 on
both calls and the returned bytes identical to the bytes sent.
Source: Amazon S3 API Reference, PutObject and GetObject.

### S3-02: User metadata and content type round-trip
Put an object with ContentType "text/plain; charset=utf-8" and user
metadata {"origin": "emulation-lab", "batch": "07"}. Expectation:
head_object reports the same ContentType and the same metadata dict.
Source: Amazon S3 User Guide, "Object metadata"; PutObject API
reference (x-amz-meta- headers).

### S3-03: Object tagging round-trip
put_object_tagging with two tags, then get_object_tagging.
Expectation: the returned tag set equals the set sent, as key and
value pairs.
Source: Amazon S3 API Reference, PutObjectTagging and
GetObjectTagging.

### S3-04: Versioning state and per-version reads
Enable versioning on a bucket. Expectation: get_bucket_versioning
then reports Status "Enabled". Put the same key twice with different
bodies. Expectation: the two responses carry two different VersionId
values; get_object with each VersionId returns that version's body;
a plain get_object returns the second body; list_object_versions
lists both version ids for the key.
Source: Amazon S3 User Guide, "Using versioning in S3 buckets".

### S3-05: Reading a deleted version fails with NoSuchVersion
On a versioning-enabled bucket, delete one version by version id,
then get_object with that version id. Expectation: the call fails
with error code NoSuchVersion.
Source: Amazon S3 API Reference, GetObject error codes; Amazon S3
error code list (NoSuchVersion: "The specified version does not
exist").

### S3-06: Error codes for a missing bucket and a missing key
get_object on a key in a bucket that was never created fails with
error code NoSuchBucket and HTTP status 404. get_object on a missing
key in an existing bucket fails with error code NoSuchKey and HTTP
status 404.
Source: Amazon S3 error code list (NoSuchBucket, NoSuchKey).

### S3-07: Deleting a key that does not exist succeeds
delete_object for a key that was never written, in an existing
bucket. Expectation: the call succeeds with HTTP status 204 and no
error. S3 delete is idempotent for keys: the documented response to
deleting an object that is not there is success.
Source: Amazon S3 API Reference, DeleteObject.

### S3-08: ListObjectsV2 pagination is complete and non-overlapping
Write 25 objects. List with MaxKeys 10 through the paginator.
Expectation: every page but the last reports IsTruncated true; the
union of returned keys is exactly the 25 written keys, with no key
returned twice.
Source: Amazon S3 API Reference, ListObjectsV2 (IsTruncated,
NextContinuationToken).

### S3-09: A presigned GET URL works without credentials
generate_presigned_url for get_object with ExpiresIn 600.
Expectation: the URL query carries X-Amz-Algorithm
"AWS4-HMAC-SHA256", X-Amz-Credential, X-Amz-Date, X-Amz-Expires
"600", X-Amz-SignedHeaders and X-Amz-Signature; an unauthenticated
HTTP GET of the URL returns HTTP 200 and the exact object bytes.
Source: Amazon S3 User Guide, "Download and upload objects with
presigned URLs".

### S3-10: A wrong Content-MD5 is rejected with BadDigest
put_object with a ContentMD5 header whose digest does not match the
body. Expectation: the call fails with error code BadDigest, and a
subsequent get_object for the key fails with NoSuchKey (nothing was
stored).
Source: Amazon S3 error code list (BadDigest: "The Content-MD5 you
specified did not match what we received").

### S3-11: A Range GET returns the requested bytes with 206
For an 11-byte object, get_object with Range "bytes=2-5".
Expectation: HTTP status 206, ContentRange "bytes 2-5/11", and the
body is bytes 2 through 5 of the object (4 bytes).
Source: Amazon S3 API Reference, GetObject (Range request header).

### S3-12: S3 Select runs a SQL query over a CSV object
Write a CSV object with a header row and 4 data rows.
select_object_content with the expression
"SELECT * FROM S3Object WHERE CAST(s._2 AS INTEGER) > 20" and CSV
input and output serializations. Expectation: the event stream
returns records containing exactly the rows whose second column
exceeds 20.
Source: Amazon S3 User Guide, "Selecting content of an object";
Amazon S3 API Reference, SelectObjectContent.

## SQS

### Q-01: Send, receive and delete round-trip, with body MD5
Send a message. Expectation: the send response MD5OfMessageBody
equals the MD5 hex digest of the body; receive_message returns the
message with the exact body; after delete_message, a further receive
returns no message.
Source: Amazon SQS API Reference, SendMessage, ReceiveMessage,
DeleteMessage.

### Q-02: Visibility timeout hides, then reveals (H3 row)
Queue with VisibilityTimeout 2 (seconds). Send one message, receive
it and do not delete it. Expectation: an immediate second receive
returns no message; after waiting 3.5 seconds, a third receive
returns the same message id.
Source: Amazon SQS Developer Guide, "Amazon SQS visibility timeout"
(verified live 2026-11-08).

### Q-03: ChangeMessageVisibility to 0 releases the message at once
Receive a message from a queue with VisibilityTimeout 60, then
change_message_visibility with VisibilityTimeout 0. Expectation: an
immediate receive returns the same message id, without waiting.
Source: Amazon SQS Developer Guide, "Amazon SQS visibility
timeout", section "Changing and terminating visibility timeout"
(verified live 2026-11-08).

### Q-04: Dead-letter redrive after maxReceiveCount (H3 row)
Queue with VisibilityTimeout 1 and a RedrivePolicy naming a
dead-letter queue with maxReceiveCount 2. Send one message; receive
it and never delete it, repeating after each visibility expiry, up
to 6 receives. Expectation: the message stops being returned by the
source queue, and receive on the dead-letter queue returns the
original body.
Source: Amazon SQS Developer Guide, "Using dead-letter queues in
Amazon SQS" (verified live 2026-11-08).

### Q-05: Long polling waits on an empty queue
Queue with ReceiveMessageWaitTimeSeconds 0. Call receive_message
with WaitTimeSeconds 5 on the empty queue. Expectation: the call
takes at least 4.0 seconds to return, and returns no message.
Source: Amazon SQS Developer Guide, "Amazon SQS short and long
polling" (long polling waits until a message is available or the
wait time expires).

### Q-06: FIFO deduplication suppresses the duplicate
FIFO queue (name ending .fifo) with content-based deduplication
off. Send a message with MessageGroupId "g1" and
MessageDeduplicationId "dup-1"; send the identical send again.
Expectation: both sends succeed; receiving with a visibility
timeout of 0 and deleting between receives yields the body exactly
once across two receives.
Source: Amazon SQS Developer Guide, "FIFO queues", message
deduplication section (a duplicate sent within the 5-minute window
is accepted but not delivered).

### Q-07: FIFO messages in one group arrive in send order
FIFO queue. Send three messages to group "g-order" with bodies
"first", "second", "third" and distinct deduplication ids.
Expectation: one receive with MaxNumberOfMessages 10 returns them
in that order.
Source: Amazon SQS Developer Guide, "FIFO queues" (messages in a
group are returned in order).

### Q-08: Receiving from a missing queue names the error
receive_message against a queue URL whose queue was deleted (queue
created, URL captured, queue deleted). Expectation: the call fails
with error code "AWS.SimpleQueueService.NonExistentQueue".
Source: Amazon SQS API Reference, error list (NonExistentQueue).

### Q-09: Message attribute round-trip and documented MD5
Send a message with two attributes: "kind" (String, value "lab")
and "count" (Number, value "42"). Expectation: receive returns both
attributes with the same values and data types, and the send
response's MD5OfMessageAttributes equals the MD5 computed by the
documented algorithm: for each attribute in name order, append the
4-byte big-endian length and bytes of the name, the 4-byte length
and bytes of the data type, one transport byte (1 for String and
Number, 2 for Binary), and the 4-byte length and bytes of the
value; MD5 over the concatenation.
Source: Amazon SQS Developer Guide, "Message attributes", MD5
checksum section.

## Lambda

The function package is a zip built in memory by the harness,
containing one Python file with two handlers: `ok_handler`, which
returns the event under the key "echo", and `fail_handler`, which
raises RuntimeError with the message "boom-failure-marker". Runtime
is python3.12. The role is the placeholder ARN
arn:aws:iam::123456789012:role/placeholder-role.

### L-01: Create a function and read its configuration back
create_function with the zip, handler lambda_function.ok_handler.
Expectation: the call succeeds; get_function returns Configuration
with the same FunctionName, Runtime "python3.12" and Handler.
Source: AWS Lambda API Reference, CreateFunction and GetFunction.

### L-02: A synchronous invoke executes the handler
invoke with InvocationType RequestResponse and payload
{"probe": "emulation"}. Expectation: HTTP status 200 in the invoke
response metadata, no FunctionError field, and the payload parses
as JSON equal to {"echo": {"probe": "emulation"}}.
Source: AWS Lambda API Reference, Invoke.

### L-03: A failing handler reports FunctionError, not an HTTP error
invoke the fail handler. Expectation: the invoke response carries
FunctionError "Handled", the HTTP status is 200, and the payload is
JSON containing errorMessage "boom-failure-marker" and errorType
naming RuntimeError.
Source: AWS Lambda API Reference, Invoke (FunctionError semantics:
handled errors return HTTP 200 with the error in the payload).

### L-04: Invoking a missing function returns ResourceNotFoundException
invoke a function name that was never created. Expectation: the
call fails with error code ResourceNotFoundException and HTTP
status 404.
Source: AWS Lambda API Reference, Invoke, Errors.

### L-05: An invalid runtime is rejected at create time
create_function with Runtime "python2.7-removed-runtime" (a runtime
string that does not exist). Expectation: the call fails with error
code InvalidParameterValueException.
Source: AWS Lambda API Reference, CreateFunction, Errors
(InvalidParameterValueException for an invalid runtime or handler).

### L-06: Reserved concurrency round-trips
put_function_concurrency with ReservedConcurrentExecutions 3 on the
created function, then get_function. Expectation: the response
Concurrency.ReservedConcurrentExecutions equals 3.
Source: AWS Lambda API Reference, PutFunctionConcurrency and
GetFunction.

### L-07: Delete removes the function from the control plane
delete_function, then get_function and list_functions.
Expectation: get_function fails with ResourceNotFoundException, and
the function name does not appear in list_functions.
Source: AWS Lambda API Reference, DeleteFunction and GetFunction.

## Failure study

### F-01: Redrive under a consumer that never deletes
Separate queue pair from Q-04: source VisibilityTimeout 1,
RedrivePolicy maxReceiveCount 3. A loop receives and never deletes,
up to 8 receives with waits for visibility expiry. Expectation:
ApproximateReceiveCount climbs to 3, the message is then moved to
the dead-letter queue, the source returns nothing further, and the
dead-letter queue returns the original body.
Source: Amazon SQS Developer Guide, "Using dead-letter queues in
Amazon SQS" (verified live 2026-11-08).

### F-02: Racing writers on a versioned bucket, then a delete marker
Versioning-enabled bucket. Writer A puts body "alpha" for key
"race"; writer B puts body "beta" for the same key. Expectation:
both version ids remain readable and return their own bodies; a
plain get returns "beta". Then delete_object without a version id.
Expectation: a plain get now fails with HTTP 404; list_object_versions
shows a delete marker as the latest entry; deleting the delete
marker by its version id makes a plain get return "beta" again.
Source: Amazon S3 User Guide, "Using versioning in S3 buckets"
(delete marker semantics).
