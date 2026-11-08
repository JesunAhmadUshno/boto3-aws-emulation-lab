"""The scored run. Starts one fresh moto server, executes every
frozen row once, and writes the raw records to results/scores.json
plus the environment to results/versions.json. Verdicts are not
computed here; scripts/make_results.py does that from the records.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import runner  # noqa: E402
from scripts.write_versions import collect  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    records = runner.run_all()
    scores_path = os.path.join(REPO, "results", "scores.json")
    with open(scores_path, "w") as fh:
        json.dump(records, fh, indent=1)
    versions_path = os.path.join(REPO, "results", "versions.json")
    with open(versions_path, "w") as fh:
        json.dump(collect(), fh, indent=1, sort_keys=True)
    for rec in records:
        print("%-6s %-7s %s" % (rec["id"], rec["service"], rec["status"]))
    print("wrote", scores_path)


if __name__ == "__main__":
    main()
