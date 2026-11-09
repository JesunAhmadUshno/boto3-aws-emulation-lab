"""Rescore named rows only (PREREGISTRATION.md Section 5): run them
against a fresh server and replace their records in
results/scores.json. Untouched rows keep their original records.
Each replaced record is appended, dated, to results/replaced-records.json
(append-only), and each new record carries a "rerun:" note, as Section 5
asks (DECISIONS.md D7).

Usage: python scripts/rerun_rows.py S3-09 S3-12 L-02 L-03
"""

import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import runner  # noqa: E402
from src.factory import EmulationServer, ensure_execution_role, make_clients, make_session  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPLACED = "results/replaced-records.json"


def merge(records, fresh, replaced, day):
    """Return (merged records, replaced log). Each fresh record replaces
    the record with its id and gains a rerun note; the old record is
    appended to the replaced log with the date, never dropped."""
    merged = []
    replaced = list(replaced)
    for rec in records:
        new = fresh.get(rec["id"])
        if new is None:
            merged.append(rec)
            continue
        replaced.append({"replaced_on": day, "record": rec})
        new = dict(new, notes=list(new["notes"]) + [
            "rerun: %s by scripts/rerun_rows.py; previous record (%s) kept in %s"
            % (day, rec["status"], REPLACED)])
        merged.append(new)
    return merged, replaced


def main(row_ids):
    wanted = {rid.upper() for rid in row_ids}
    by_name = {fn.__name__.upper().replace("_", "-"): fn for fn in runner.ROW_FUNCTIONS}
    unknown = wanted - set(by_name)
    if unknown:
        raise SystemExit("unknown row ids: %s" % sorted(unknown))
    scores_path = os.path.join(REPO, "results", "scores.json")
    with open(scores_path) as fh:
        records = json.load(fh)
    fresh = {}
    with EmulationServer() as server:
        clients = make_clients(make_session(), server.endpoint_url)
        ctx = runner.Context(clients, server.endpoint_url)
        ctx.role_arn = ensure_execution_role(clients)
        for rid in sorted(wanted):
            fresh[rid] = runner._run_one(ctx, by_name[rid])
    replaced_path = os.path.join(REPO, REPLACED)
    replaced = []
    if os.path.exists(replaced_path):
        with open(replaced_path) as fh:
            replaced = json.load(fh)
    day = datetime.date.today().isoformat()
    merged, replaced = merge(records, fresh, replaced, day)
    with open(replaced_path, "w") as fh:
        json.dump(replaced, fh, indent=1)
    with open(scores_path, "w") as fh:
        json.dump(merged, fh, indent=1)
    for rid in sorted(wanted):
        print("%-6s %s" % (rid, fresh[rid]["status"]))
    print("merged into", scores_path)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("usage: rerun_rows.py ROW-ID [ROW-ID ...]")
    main(sys.argv[1:])
