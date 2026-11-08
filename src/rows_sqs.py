"""SQS behaviour rows Q-01 to Q-09 and failure row F-01."""

import json
import time

from botocore.exceptions import ClientError

from .oracles import md5_hex_of_body, md5_of_message_attributes
from .records import RowRecord


def _queue(ctx, attributes=None, fifo=False):
    sqs = ctx.clients["sqs"]
    name = "emu-%s%s" % (ctx.suffix(), ".fifo" if fifo else "")
    attrs = dict(attributes or {})
    if fifo:
        attrs["FifoQueue"] = "true"
    url = sqs.create_queue(QueueName=name, Attributes=attrs)["QueueUrl"]
    return url


def _queue_arn(ctx, url):
    sqs = ctx.clients["sqs"]
    return sqs.get_queue_attributes(QueueUrl=url, AttributeNames=["QueueArn"])[
        "Attributes"
    ]["QueueArn"]


def _receive(sqs, url, **kwargs):
    kwargs.setdefault("MaxNumberOfMessages", 1)
    kwargs.setdefault("WaitTimeSeconds", 0)
    return sqs.receive_message(QueueUrl=url, **kwargs).get("Messages", [])


def q_01(ctx):
    rec = RowRecord("Q-01", "sqs")
    sqs = ctx.clients["sqs"]
    url = _queue(ctx)
    body = "round-trip body"
    sent = sqs.send_message(QueueUrl=url, MessageBody=body)
    rec.check("body md5", md5_hex_of_body(body), sent.get("MD5OfMessageBody"))
    msgs = _receive(sqs, url)
    rec.check("one message", 1, len(msgs))
    if msgs:
        rec.check("body intact", body, msgs[0]["Body"])
        sqs.delete_message(QueueUrl=url, ReceiptHandle=msgs[0]["ReceiptHandle"])
    rec.check("empty after delete", 0, len(_receive(sqs, url)))
    return rec


def q_02(ctx):
    rec = RowRecord("Q-02", "sqs")
    sqs = ctx.clients["sqs"]
    url = _queue(ctx, {"VisibilityTimeout": "2"})
    sqs.send_message(QueueUrl=url, MessageBody="visibility probe")
    first = _receive(sqs, url)
    rec.check("first receive", 1, len(first))
    second = _receive(sqs, url)
    rec.check("hidden while in flight", 0, len(second))
    time.sleep(3.5)
    third = _receive(sqs, url)
    rec.check("revealed after timeout", 1, len(third))
    if first and third:
        rec.check(
            "same message id",
            first[0]["MessageId"],
            third[0]["MessageId"],
        )
    return rec


def q_03(ctx):
    rec = RowRecord("Q-03", "sqs")
    sqs = ctx.clients["sqs"]
    url = _queue(ctx, {"VisibilityTimeout": "60"})
    sqs.send_message(QueueUrl=url, MessageBody="release probe")
    first = _receive(sqs, url)
    rec.check("first receive", 1, len(first))
    if first:
        sqs.change_message_visibility(
            QueueUrl=url,
            ReceiptHandle=first[0]["ReceiptHandle"],
            VisibilityTimeout=0,
        )
    second = _receive(sqs, url)
    rec.check("visible again at once", 1, len(second))
    if first and second:
        rec.check("same message id", first[0]["MessageId"], second[0]["MessageId"])
    return rec


def _redrive_pair(ctx, max_receive_count):
    sqs = ctx.clients["sqs"]
    dlq_url = _queue(ctx)
    dlq_arn = _queue_arn(ctx, dlq_url)
    policy = json.dumps(
        {"deadLetterTargetArn": dlq_arn, "maxReceiveCount": str(max_receive_count)}
    )
    src_url = _queue(
        ctx, {"VisibilityTimeout": "1", "RedrivePolicy": policy}
    )
    return src_url, dlq_url


def q_04(ctx):
    rec = RowRecord("Q-04", "sqs")
    sqs = ctx.clients["sqs"]
    src_url, dlq_url = _redrive_pair(ctx, 2)
    body = "redrive probe"
    sqs.send_message(QueueUrl=src_url, MessageBody=body)
    receives = 0
    for _ in range(6):
        msgs = _receive(sqs, src_url)
        if not msgs:
            break
        receives += 1
        time.sleep(1.4)
    rec.note("source receives before the message moved: %d" % receives)
    rec.check("source drained", 0, len(_receive(sqs, src_url)))
    dlq_msgs = _receive(sqs, dlq_url)
    rec.check("message in dlq", 1, len(dlq_msgs))
    if dlq_msgs:
        rec.check("dlq body intact", body, dlq_msgs[0]["Body"])
    return rec


def q_05(ctx):
    rec = RowRecord("Q-05", "sqs")
    sqs = ctx.clients["sqs"]
    url = _queue(ctx, {"ReceiveMessageWaitTimeSeconds": "0"})
    start = time.monotonic()
    msgs = sqs.receive_message(QueueUrl=url, WaitTimeSeconds=5).get("Messages", [])
    elapsed = time.monotonic() - start
    rec.check("no message on empty queue", 0, len(msgs))
    rec.check(
        "long poll waits at least 4.0 s",
        True,
        elapsed >= 4.0,
        ok=None,
    )
    rec.assertions[-1]["observed"] = "%.2f s elapsed" % elapsed
    rec.assertions[-1]["expected"] = ">= 4.0 s elapsed"
    return rec


def q_06(ctx):
    rec = RowRecord("Q-06", "sqs")
    sqs = ctx.clients["sqs"]
    url = _queue(ctx, {"ContentBasedDeduplication": "false"}, fifo=True)
    body = "dedup probe"
    send_ok = True
    try:
        for _ in range(2):
            sqs.send_message(
                QueueUrl=url,
                MessageBody=body,
                MessageGroupId="g1",
                MessageDeduplicationId="dup-1",
            )
    except ClientError:
        send_ok = False
    rec.check("both sends accepted", True, send_ok)
    seen = []
    for _ in range(2):
        msgs = _receive(sqs, url, MaxNumberOfMessages=10)
        for msg in msgs:
            seen.append(msg["Body"])
            sqs.delete_message(QueueUrl=url, ReceiptHandle=msg["ReceiptHandle"])
    rec.check("body delivered exactly once", 1, seen.count(body))
    return rec


def q_07(ctx):
    rec = RowRecord("Q-07", "sqs")
    sqs = ctx.clients["sqs"]
    url = _queue(ctx, {"ContentBasedDeduplication": "false"}, fifo=True)
    bodies = ["first", "second", "third"]
    for i, body in enumerate(bodies):
        sqs.send_message(
            QueueUrl=url,
            MessageBody=body,
            MessageGroupId="g-order",
            MessageDeduplicationId="ord-%d" % i,
        )
    msgs = _receive(sqs, url, MaxNumberOfMessages=10)
    rec.check("group order preserved", bodies, [m["Body"] for m in msgs])
    return rec


def q_08(ctx):
    rec = RowRecord("Q-08", "sqs")
    sqs = ctx.clients["sqs"]
    url = _queue(ctx)
    sqs.delete_queue(QueueUrl=url)
    time.sleep(1.0)
    try:
        sqs.receive_message(QueueUrl=url)
        rec.check("missing queue fails", "ClientError", "no error")
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code")
        rec.check(
            "error code", "AWS.SimpleQueueService.NonExistentQueue", code
        )
    return rec


def q_09(ctx):
    rec = RowRecord("Q-09", "sqs")
    sqs = ctx.clients["sqs"]
    url = _queue(ctx)
    attributes = {
        "kind": {"DataType": "String", "StringValue": "lab"},
        "count": {"DataType": "Number", "StringValue": "42"},
    }
    sent = sqs.send_message(
        QueueUrl=url, MessageBody="attribute probe", MessageAttributes=attributes
    )
    rec.check(
        "attribute md5 (documented algorithm)",
        md5_of_message_attributes(attributes),
        sent.get("MD5OfMessageAttributes"),
    )
    msgs = sqs.receive_message(
        QueueUrl=url, MessageAttributeNames=["All"], MaxNumberOfMessages=1
    ).get("Messages", [])
    rec.check("one message", 1, len(msgs))
    if msgs:
        got = msgs[0].get("MessageAttributes", {})
        for name, want in attributes.items():
            have = got.get(name, {})
            rec.check(
                "attribute %s value" % name,
                want["StringValue"],
                have.get("StringValue"),
            )
            rec.check(
                "attribute %s type" % name, want["DataType"], have.get("DataType")
            )
    return rec


def f_01(ctx):
    rec = RowRecord("F-01", "sqs")
    sqs = ctx.clients["sqs"]
    src_url, dlq_url = _redrive_pair(ctx, 3)
    body = "poison probe"
    sqs.send_message(QueueUrl=src_url, MessageBody=body)
    receives = 0
    for _ in range(8):
        msgs = sqs.receive_message(
            QueueUrl=src_url,
            MaxNumberOfMessages=1,
            AttributeNames=["ApproximateReceiveCount"],
        ).get("Messages", [])
        if not msgs:
            break
        receives += 1
        time.sleep(1.4)
    rec.check("received exactly 3 times before moving", 3, receives)
    rec.check("source drained", 0, len(_receive(sqs, src_url)))
    dlq_msgs = _receive(sqs, dlq_url)
    rec.check("message in dlq", 1, len(dlq_msgs))
    if dlq_msgs:
        rec.check("dlq body intact", body, dlq_msgs[0]["Body"])
    return rec


ROWS = [q_01, q_02, q_03, q_04, q_05, q_06, q_07, q_08, q_09, f_01]
