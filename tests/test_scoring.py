"""Classifier and verdict rules, tested on fabricated records only."""

from scripts.make_results import verdicts
from src.oracles import md5_hex_of_body, md5_of_message_attributes
from src.records import RowRecord, classify


def _record(row_id, service, status):
    rec = RowRecord(row_id, service)
    if status == "MATCHES":
        rec.check("a", 1, 1)
    elif status == "DIVERGES":
        rec.check("a", 1, 2)
    elif status == "UNSUPPORTED":
        rec.mark_unsupported("fake refusal")
    elif status == "ERROR":
        rec.harness_error = "fake crash"
    out = rec.to_dict()
    assert out["status"] == status
    return out


def test_classifier_vocabulary():
    assert classify(_bare("MATCHES")) == "MATCHES"
    assert classify(_bare("DIVERGES")) == "DIVERGES"
    assert classify(_bare("UNSUPPORTED")) == "UNSUPPORTED"
    assert classify(RowRecord("X-99", "s3")) == "ERROR"


def _bare(status):
    rec = RowRecord("X-00", "s3")
    if status == "MATCHES":
        rec.check("a", 1, 1)
    elif status == "DIVERGES":
        rec.check("a", 1, 2)
    elif status == "UNSUPPORTED":
        rec.mark_unsupported("fake refusal")
    return rec


def _rows(statuses):
    services = ["s3"] * 13 + ["sqs"] * 10 + ["lambda"] * 7
    ids = (
        ["S3-%02d" % i for i in range(1, 14)]
        + ["Q-%02d" % i for i in range(1, 11)]
        + ["L-%02d" % i for i in range(1, 8)]
    )
    return [
        _record(rid, svc, status)
        for rid, svc, status in zip(ids, services, statuses)
    ]


def test_h1_line_at_70_percent():
    rows = _rows(["MATCHES"] * 21 + ["DIVERGES"] * 9)
    assert verdicts(rows)["H1"] == "CONFIRMED"
    rows = _rows(["MATCHES"] * 20 + ["DIVERGES"] * 10)
    assert verdicts(rows)["H1"] == "REFUTED"


def test_h3_needs_both_rows():
    rows = _rows(["MATCHES"] * 30)
    v = verdicts(rows)
    assert v["H3"] == "CONFIRMED"
    rows[14] = _record("Q-02", "sqs", "DIVERGES")  # index of Q-02
    assert verdicts(rows)["H3"] == "REFUTED"


def test_error_row_forces_inconclusive():
    rows = _rows(["MATCHES"] * 30)
    rows[0] = _record("S3-01", "s3", "ERROR")
    v = verdicts(rows)
    assert v["H1"] == "INCONCLUSIVE"
    assert v["H2"] == "INCONCLUSIVE"


def test_attribute_md5_oracle_properties():
    attrs_a = {
        "kind": {"DataType": "String", "StringValue": "lab"},
        "count": {"DataType": "Number", "StringValue": "42"},
    }
    attrs_b = {
        "count": {"DataType": "Number", "StringValue": "42"},
        "kind": {"DataType": "String", "StringValue": "lab"},
    }
    # The documented algorithm sorts by attribute name, so insertion
    # order must not change the checksum.
    assert md5_of_message_attributes(attrs_a) == md5_of_message_attributes(attrs_b)
    changed = {
        "kind": {"DataType": "String", "StringValue": "lab"},
        "count": {"DataType": "Number", "StringValue": "43"},
    }
    assert md5_of_message_attributes(attrs_a) != md5_of_message_attributes(changed)


def test_body_md5_known_vector():
    # MD5 of the empty string is a fixed public constant.
    assert md5_hex_of_body("") == "d41d8cd98f00b204e9800998ecf8427e"
