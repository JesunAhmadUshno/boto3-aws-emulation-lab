"""Per-row record keeping and the scoring classifier.

A row function fills a RowRecord with assertions. Each assertion has
a name, the documented expected value, the observed value, and
whether they agree. The classifier in this module turns a record
into MATCHES, DIVERGES, UNSUPPORTED or ERROR under the frozen rules
of PREREGISTRATION.md Section 5.
"""


class RowRecord:
    def __init__(self, row_id, service):
        self.id = row_id
        self.service = service
        self.assertions = []
        self.notes = []
        self.unsupported_text = None
        self.harness_error = None

    def check(self, name, expected, observed, ok=None):
        if ok is None:
            ok = expected == observed
        self.assertions.append(
            {
                "name": name,
                "expected": _short(expected),
                "observed": _short(observed),
                "ok": bool(ok),
            }
        )
        return bool(ok)

    def note(self, text):
        self.notes.append(str(text))

    def mark_unsupported(self, text):
        self.unsupported_text = str(text)

    def to_dict(self):
        return {
            "id": self.id,
            "service": self.service,
            "assertions": self.assertions,
            "notes": self.notes,
            "unsupported_text": self.unsupported_text,
            "harness_error": self.harness_error,
            "status": classify(self),
        }


def _short(value, limit=300):
    text = repr(value)
    if len(text) > limit:
        text = text[:limit] + "...[truncated]"
    return text


def looks_unsupported(exc):
    """True when an exception reads as the emulator refusing the
    operation as not implemented or unsupported."""
    text = "%s: %s" % (type(exc).__name__, exc)
    lowered = text.lower()
    return (
        isinstance(exc, NotImplementedError)
        or "notimplemented" in lowered.replace(" ", "").replace("_", "")
        or "not implemented" in lowered
        or "not supported" in lowered
        or "unsupported" in lowered
    )


def classify(record):
    if record.harness_error:
        return "ERROR"
    if record.unsupported_text:
        return "UNSUPPORTED"
    if record.assertions and all(a["ok"] for a in record.assertions):
        return "MATCHES"
    if not record.assertions:
        return "ERROR"
    return "DIVERGES"
