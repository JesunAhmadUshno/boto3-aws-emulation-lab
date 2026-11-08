"""Smoke: three fast rows execute end to end against a live local
moto server, with no sleeps, so CI stays quick. The scored run is
scripts/run_study.py, not this test.
"""

from src import rows_lambda, rows_s3, rows_sqs
from src.factory import (
    EmulationServer,
    ensure_execution_role,
    make_clients,
    make_session,
)
from src.runner import Context

VOCABULARY = ("MATCHES", "DIVERGES", "UNSUPPORTED", "ERROR")


def _ctx():
    server = EmulationServer()
    server.__enter__()
    clients = make_clients(make_session(), server.endpoint_url)
    ctx = Context(clients, server.endpoint_url)
    ctx.role_arn = ensure_execution_role(clients)
    return server, ctx


def test_smoke_rows():
    server, ctx = _ctx()
    try:
        s3_rec = rows_s3.s3_01(ctx).to_dict()
        sqs_rec = rows_sqs.q_01(ctx).to_dict()
        lam_rec = rows_lambda.l_01(ctx).to_dict()
    finally:
        server.__exit__()
    assert s3_rec["status"] == "MATCHES"
    assert sqs_rec["status"] == "MATCHES"
    assert lam_rec["status"] in VOCABULARY
    assert lam_rec["assertions"] or lam_rec["unsupported_text"]
