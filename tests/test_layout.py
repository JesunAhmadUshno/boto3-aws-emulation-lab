"""Portfolio standard checks: the lock holds, the required files exist,
no grade is public, and the README headline traces to the evidence."""
import glob
import hashlib
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# SHA-256 as committed: PREREGISTRATION.md in 2b2659d (root commit, tag
# proposal-v1), BEHAVIOURS.md in 28bfcf2; both before any code or run.
LOCKED_SHA256 = {
    "PREREGISTRATION.md": "4ddb109e2d0ec0f7f6336bbf29f2c787f268ebb114e2a2866093d84b0e490dec",
    "BEHAVIOURS.md": "d1de53d50028be6b7b5131c114d7a123b3134dfeb801f5139c41034ff65f29e3",
}
GRADE = re.compile(r"of 10,?000|/ ?10,?000|Grade:|graded out of", re.I)


def _read(name):
    with open(os.path.join(ROOT, name), "rb") as f:
        return f.read()


def test_locked_files_are_unchanged_since_the_lock():
    for name, want in LOCKED_SHA256.items():
        assert hashlib.sha256(_read(name)).hexdigest() == want, \
            name + " changed after its lock; record an amendment in DECISIONS.md instead"


def test_required_files_exist():
    need = ["README.md", "PREREGISTRATION.md", "BEHAVIOURS.md", "AUDIT.md", "RESULTS.md",
            "DECISIONS.md", "CHANGELOG.md", "CITATION.cff", "SECURITY.md", "LICENSE",
            "results/scores.json", "results/versions.json", "results/summary.json"]
    missing = [p for p in need if not os.path.exists(os.path.join(ROOT, p))]
    assert not missing, "missing: " + ", ".join(missing)


def test_no_public_grade():
    public = glob.glob(os.path.join(ROOT, "*.md")) + [os.path.join(ROOT, "CITATION.cff")]
    for path in public:
        text = open(path, encoding="utf-8").read()
        assert not GRADE.search(text), os.path.basename(path) + " carries a grade; grades are internal"


def test_readme_headline_matches_summary():
    summary = json.loads(_read("results/summary.json"))["verdicts"]
    readme = _read("README.md").decode("utf-8")
    headline = readme.split("**Headline.**", 1)[1].split("**Field.**", 1)[0]
    headline = " ".join(headline.split())
    assert "%d of %d" % (summary["matches"], summary["total_rows"]) in headline
    assert "%.1f percent" % (100 * summary["share_matches"]) in headline
    for h in ("H1", "H2", "H3"):
        assert "%s %s" % (h, summary[h]) in headline, h
