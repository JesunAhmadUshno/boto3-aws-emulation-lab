"""Failure study row F-02: racing writers on a versioned bucket."""

from botocore.exceptions import ClientError

from .records import RowRecord


def f_02(ctx):
    rec = RowRecord("F-02", "s3")
    s3 = ctx.clients["s3"]
    bucket = "emu-%s" % ctx.suffix()
    s3.create_bucket(Bucket=bucket)
    s3.put_bucket_versioning(
        Bucket=bucket, VersioningConfiguration={"Status": "Enabled"}
    )
    va = s3.put_object(Bucket=bucket, Key="race", Body=b"alpha")["VersionId"]
    vb = s3.put_object(Bucket=bucket, Key="race", Body=b"beta")["VersionId"]
    rec.check(
        "writer A version body",
        b"alpha",
        s3.get_object(Bucket=bucket, Key="race", VersionId=va)["Body"].read(),
    )
    rec.check(
        "writer B version body",
        b"beta",
        s3.get_object(Bucket=bucket, Key="race", VersionId=vb)["Body"].read(),
    )
    rec.check(
        "plain get returns latest writer",
        b"beta",
        s3.get_object(Bucket=bucket, Key="race")["Body"].read(),
    )
    deleted = s3.delete_object(Bucket=bucket, Key="race")
    marker_id = deleted.get("VersionId")
    rec.check("delete marker created", True, bool(deleted.get("DeleteMarker")))
    try:
        s3.get_object(Bucket=bucket, Key="race")
        rec.check("plain get after delete marker fails", "404 error", "no error")
    except ClientError as exc:
        status = exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
        code = exc.response.get("Error", {}).get("Code")
        rec.check("plain get after delete marker: status", 404, status)
        rec.note("error code observed: %s" % code)
    listing = s3.list_object_versions(Bucket=bucket, Prefix="race")
    markers = listing.get("DeleteMarkers", [])
    rec.check("delete marker listed", 1, len(markers))
    if markers and marker_id:
        rec.check(
            "listed marker id matches delete response",
            marker_id,
            markers[0]["VersionId"],
        )
        s3.delete_object(Bucket=bucket, Key="race", VersionId=marker_id)
        rec.check(
            "plain get restored after marker removal",
            b"beta",
            s3.get_object(Bucket=bucket, Key="race")["Body"].read(),
        )
    return rec


ROWS = [f_02]
