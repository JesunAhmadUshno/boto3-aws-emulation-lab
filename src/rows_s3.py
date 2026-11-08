"""S3 behaviour rows S3-01 to S3-12, implementing BEHAVIOURS.md."""

import hashlib
import io
import urllib.parse

import requests
from botocore.exceptions import ClientError

from .records import RowRecord, looks_unsupported


def err_info(exc):
    if isinstance(exc, ClientError):
        return (
            exc.response.get("Error", {}).get("Code"),
            exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode"),
            str(exc),
        )
    return (type(exc).__name__, None, str(exc))


def _bucket(ctx, versioning=False):
    s3 = ctx.clients["s3"]
    name = "emu-%s" % ctx.suffix()
    s3.create_bucket(Bucket=name)
    if versioning:
        s3.put_bucket_versioning(
            Bucket=name, VersioningConfiguration={"Status": "Enabled"}
        )
    return name


def s3_01(ctx):
    rec = RowRecord("S3-01", "s3")
    s3 = ctx.clients["s3"]
    bucket = _bucket(ctx)
    body = bytes(range(256)) * 4
    put = s3.put_object(Bucket=bucket, Key="blob", Body=body)
    rec.check("put status", 200, put["ResponseMetadata"]["HTTPStatusCode"])
    got = s3.get_object(Bucket=bucket, Key="blob")
    data = got["Body"].read()
    rec.check("get status", 200, got["ResponseMetadata"]["HTTPStatusCode"])
    rec.check("byte equality", True, data == body)
    return rec


def s3_02(ctx):
    rec = RowRecord("S3-02", "s3")
    s3 = ctx.clients["s3"]
    bucket = _bucket(ctx)
    meta = {"origin": "emulation-lab", "batch": "07"}
    s3.put_object(
        Bucket=bucket,
        Key="doc",
        Body=b"metadata probe",
        ContentType="text/plain; charset=utf-8",
        Metadata=meta,
    )
    head = s3.head_object(Bucket=bucket, Key="doc")
    rec.check("content type", "text/plain; charset=utf-8", head.get("ContentType"))
    rec.check("user metadata", meta, head.get("Metadata"))
    return rec


def s3_03(ctx):
    rec = RowRecord("S3-03", "s3")
    s3 = ctx.clients["s3"]
    bucket = _bucket(ctx)
    s3.put_object(Bucket=bucket, Key="tagged", Body=b"t")
    tags = [{"Key": "team", "Value": "research"}, {"Key": "tier", "Value": "lab"}]
    s3.put_object_tagging(Bucket=bucket, Key="tagged", Tagging={"TagSet": tags})
    got = s3.get_object_tagging(Bucket=bucket, Key="tagged")["TagSet"]
    norm = lambda ts: sorted((t["Key"], t["Value"]) for t in ts)
    rec.check("tag set", norm(tags), norm(got))
    return rec


def s3_04(ctx):
    rec = RowRecord("S3-04", "s3")
    s3 = ctx.clients["s3"]
    bucket = _bucket(ctx, versioning=True)
    status = s3.get_bucket_versioning(Bucket=bucket).get("Status")
    rec.check("versioning status", "Enabled", status)
    v1 = s3.put_object(Bucket=bucket, Key="k", Body=b"first-body")["VersionId"]
    v2 = s3.put_object(Bucket=bucket, Key="k", Body=b"second-body")["VersionId"]
    rec.check("distinct version ids", True, bool(v1) and bool(v2) and v1 != v2)
    b1 = s3.get_object(Bucket=bucket, Key="k", VersionId=v1)["Body"].read()
    b2 = s3.get_object(Bucket=bucket, Key="k", VersionId=v2)["Body"].read()
    latest = s3.get_object(Bucket=bucket, Key="k")["Body"].read()
    rec.check("version 1 body", b"first-body", b1)
    rec.check("version 2 body", b"second-body", b2)
    rec.check("plain get returns latest", b"second-body", latest)
    listed = s3.list_object_versions(Bucket=bucket, Prefix="k")
    ids = sorted(v["VersionId"] for v in listed.get("Versions", []))
    rec.check("listed version ids", sorted([v1, v2]), ids)
    return rec


def s3_05(ctx):
    rec = RowRecord("S3-05", "s3")
    s3 = ctx.clients["s3"]
    bucket = _bucket(ctx, versioning=True)
    v1 = s3.put_object(Bucket=bucket, Key="k", Body=b"gone")["VersionId"]
    s3.put_object(Bucket=bucket, Key="k", Body=b"stays")
    s3.delete_object(Bucket=bucket, Key="k", VersionId=v1)
    try:
        s3.get_object(Bucket=bucket, Key="k", VersionId=v1)
        rec.check("deleted version read fails", "ClientError", "no error")
    except ClientError as exc:
        code, status, _ = err_info(exc)
        rec.check("error code", "NoSuchVersion", code)
        rec.note("http status observed: %s" % status)
    return rec


def s3_06(ctx):
    rec = RowRecord("S3-06", "s3")
    s3 = ctx.clients["s3"]
    missing_bucket = "emu-never-created-%s" % ctx.suffix()
    try:
        s3.get_object(Bucket=missing_bucket, Key="k")
        rec.check("missing bucket fails", "ClientError", "no error")
    except ClientError as exc:
        code, status, _ = err_info(exc)
        rec.check("missing bucket code", "NoSuchBucket", code)
        rec.check("missing bucket status", 404, status)
    bucket = _bucket(ctx)
    try:
        s3.get_object(Bucket=bucket, Key="never-written")
        rec.check("missing key fails", "ClientError", "no error")
    except ClientError as exc:
        code, status, _ = err_info(exc)
        rec.check("missing key code", "NoSuchKey", code)
        rec.check("missing key status", 404, status)
    return rec


def s3_07(ctx):
    rec = RowRecord("S3-07", "s3")
    s3 = ctx.clients["s3"]
    bucket = _bucket(ctx)
    resp = s3.delete_object(Bucket=bucket, Key="never-written")
    rec.check("delete status", 204, resp["ResponseMetadata"]["HTTPStatusCode"])
    return rec


def s3_08(ctx):
    rec = RowRecord("S3-08", "s3")
    s3 = ctx.clients["s3"]
    bucket = _bucket(ctx)
    keys = ["obj-%02d" % i for i in range(25)]
    for key in keys:
        s3.put_object(Bucket=bucket, Key=key, Body=b"x")
    paginator = s3.get_paginator("list_objects_v2")
    seen = []
    truncated_flags = []
    for page in paginator.paginate(Bucket=bucket, PaginationConfig={"PageSize": 10}):
        truncated_flags.append(page.get("IsTruncated", False))
        seen.extend(item["Key"] for item in page.get("Contents", []))
    rec.check("all keys returned", sorted(keys), sorted(seen))
    rec.check("no duplicates", 25, len(seen))
    rec.check(
        "truncation flags (3 pages)",
        [True, True, False],
        truncated_flags,
    )
    return rec


def s3_09(ctx):
    rec = RowRecord("S3-09", "s3")
    s3 = ctx.clients["s3"]
    bucket = _bucket(ctx)
    body = b"presigned-body"
    s3.put_object(Bucket=bucket, Key="signed", Body=body)
    url = s3.generate_presigned_url(
        "get_object", Params={"Bucket": bucket, "Key": "signed"}, ExpiresIn=600
    )
    query = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    rec.check("algorithm param", ["AWS4-HMAC-SHA256"], query.get("X-Amz-Algorithm"))
    rec.check("expires param", ["600"], query.get("X-Amz-Expires"))
    for param in ("X-Amz-Credential", "X-Amz-Date", "X-Amz-SignedHeaders", "X-Amz-Signature"):
        rec.check("param present: %s" % param, True, param in query)
    resp = requests.get(url, timeout=15)
    rec.check("unsigned fetch status", 200, resp.status_code)
    rec.check("unsigned fetch bytes", body, resp.content)
    return rec


def s3_10(ctx):
    rec = RowRecord("S3-10", "s3")
    s3 = ctx.clients["s3"]
    bucket = _bucket(ctx)
    body = b"digest probe body"
    import base64

    wrong_md5 = base64.b64encode(hashlib.md5(b"some other body").digest()).decode("ascii")
    try:
        s3.put_object(Bucket=bucket, Key="guarded", Body=body, ContentMD5=wrong_md5)
        rec.check("bad digest rejected", "ClientError", "no error")
    except ClientError as exc:
        code, _, _ = err_info(exc)
        rec.check("error code", "BadDigest", code)
    try:
        s3.get_object(Bucket=bucket, Key="guarded")
        rec.check("nothing stored", "NoSuchKey", "object readable")
    except ClientError as exc:
        code, _, _ = err_info(exc)
        rec.check("nothing stored", "NoSuchKey", code)
    return rec


def s3_11(ctx):
    rec = RowRecord("S3-11", "s3")
    s3 = ctx.clients["s3"]
    bucket = _bucket(ctx)
    s3.put_object(Bucket=bucket, Key="ranged", Body=b"0123456789A")
    got = s3.get_object(Bucket=bucket, Key="ranged", Range="bytes=2-5")
    rec.check("range status", 206, got["ResponseMetadata"]["HTTPStatusCode"])
    rec.check("content range", "bytes 2-5/11", got.get("ContentRange"))
    rec.check("range bytes", b"2345", got["Body"].read())
    return rec


def s3_12(ctx):
    rec = RowRecord("S3-12", "s3")
    s3 = ctx.clients["s3"]
    bucket = _bucket(ctx)
    csv_body = b"name,score\nalpha,10\nbeta,25\ngamma,30\ndelta,5\n"
    s3.put_object(Bucket=bucket, Key="data.csv", Body=csv_body)
    try:
        resp = s3.select_object_content(
            Bucket=bucket,
            Key="data.csv",
            ExpressionType="SQL",
            Expression="SELECT * FROM S3Object WHERE CAST(s._2 AS INTEGER) > 20",
            InputSerialization={"CSV": {"FileHeaderInfo": "USE"}},
            OutputSerialization={"CSV": {}},
        )
    except Exception as exc:
        if looks_unsupported(exc):
            rec.mark_unsupported("%s: %s" % (type(exc).__name__, exc))
            return rec
        raise
    payload = b""
    for event in resp["Payload"]:
        if "Records" in event:
            payload += event["Records"]["Payload"]
    rows = sorted(line for line in payload.decode("utf-8").strip().splitlines() if line)
    rec.check("selected rows", ["beta,25", "gamma,30"], rows)
    return rec


ROWS = [
    s3_01, s3_02, s3_03, s3_04, s3_05, s3_06,
    s3_07, s3_08, s3_09, s3_10, s3_11, s3_12,
]
