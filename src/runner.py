"""Runs every frozen row once against a fresh emulator server and
returns the raw records. Row order is the BEHAVIOURS.md order.
"""

import uuid

from . import rows_failure, rows_lambda, rows_s3, rows_sqs
from .factory import (
    PLACEHOLDER_ROLE_ARN,
    EmulationServer,
    ensure_execution_role,
    make_clients,
    make_session,
)
from .records import RowRecord, looks_unsupported

ROW_FUNCTIONS = (
    rows_s3.ROWS + rows_sqs.ROWS + rows_lambda.ROWS + rows_failure.ROWS
)

ROW_SERVICES = {}


class Context:
    def __init__(self, clients, endpoint_url):
        self.clients = clients
        self.endpoint_url = endpoint_url
        self.role_arn = PLACEHOLDER_ROLE_ARN

    def suffix(self):
        return uuid.uuid4().hex[:10]


def run_all():
    records = []
    with EmulationServer() as server:
        session = make_session()
        clients = make_clients(session, server.endpoint_url)
        ctx = Context(clients, server.endpoint_url)
        ctx.role_arn = ensure_execution_role(clients)
        for fn in ROW_FUNCTIONS:
            records.append(_run_one(ctx, fn))
    return records


def _run_one(ctx, fn):
    # Row ids are derived from the function name (s3_01 -> S3-01,
    # q_04 -> Q-04, l_07 -> L-07, f_01 -> F-01) so that a crash
    # before the record exists still lands in a named record.
    row_id = fn.__name__.upper().replace("_", "-")
    service = {"S3": "s3", "Q": "sqs", "L": "lambda", "F": "failure"}[
        row_id.split("-")[0]
    ]
    try:
        record = fn(ctx)
        return record.to_dict()
    except Exception as exc:  # one row must never kill the run
        record = RowRecord(row_id, service)
        if looks_unsupported(exc):
            record.mark_unsupported("%s: %s" % (type(exc).__name__, exc))
        else:
            record.harness_error = "%s: %s" % (type(exc).__name__, exc)
        return record.to_dict()
