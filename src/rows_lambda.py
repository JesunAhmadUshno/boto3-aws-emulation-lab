"""Lambda behaviour rows L-01 to L-07."""

import io
import json
import zipfile

from botocore.exceptions import ClientError

from .records import RowRecord, looks_unsupported

HANDLER_SOURCE = '''
def ok_handler(event, context):
    return {"echo": event}


def fail_handler(event, context):
    raise RuntimeError("boom-failure-marker")
'''


def _zip_bytes():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("lambda_function.py", HANDLER_SOURCE)
    return buf.getvalue()


def _create(ctx, handler, runtime="python3.12"):
    lam = ctx.clients["lambda"]
    name = "emu-%s" % ctx.suffix()
    resp = lam.create_function(
        FunctionName=name,
        Runtime=runtime,
        Role=ctx.role_arn,
        Handler=handler,
        Code={"ZipFile": _zip_bytes()},
    )
    return name, resp


def _invoke(ctx, rec, name, payload):
    """Invoke; an emulator refusal at this call marks the row
    UNSUPPORTED and returns None."""
    lam = ctx.clients["lambda"]
    try:
        return lam.invoke(
            FunctionName=name,
            InvocationType="RequestResponse",
            Payload=json.dumps(payload).encode("utf-8"),
        )
    except Exception as exc:
        if looks_unsupported(exc):
            rec.mark_unsupported("%s: %s" % (type(exc).__name__, exc))
            return None
        raise


def l_01(ctx):
    rec = RowRecord("L-01", "lambda")
    lam = ctx.clients["lambda"]
    name, _ = _create(ctx, "lambda_function.ok_handler")
    conf = lam.get_function(FunctionName=name)["Configuration"]
    rec.check("function name", name, conf.get("FunctionName"))
    rec.check("runtime", "python3.12", conf.get("Runtime"))
    rec.check("handler", "lambda_function.ok_handler", conf.get("Handler"))
    return rec


def l_02(ctx):
    rec = RowRecord("L-02", "lambda")
    name, _ = _create(ctx, "lambda_function.ok_handler")
    resp = _invoke(ctx, rec, name, {"probe": "emulation"})
    if resp is None:
        return rec
    status = resp["ResponseMetadata"]["HTTPStatusCode"]
    rec.check("invoke http status", 200, status)
    rec.check("no FunctionError", None, resp.get("FunctionError"))
    payload = json.loads(resp["Payload"].read().decode("utf-8"))
    rec.check("handler response", {"echo": {"probe": "emulation"}}, payload)
    return rec


def l_03(ctx):
    rec = RowRecord("L-03", "lambda")
    name, _ = _create(ctx, "lambda_function.fail_handler")
    resp = _invoke(ctx, rec, name, {"probe": "failure"})
    if resp is None:
        return rec
    status = resp["ResponseMetadata"]["HTTPStatusCode"]
    rec.check("invoke http status", 200, status)
    rec.check("FunctionError", "Handled", resp.get("FunctionError"))
    payload = json.loads(resp["Payload"].read().decode("utf-8"))
    rec.check("errorMessage", "boom-failure-marker", payload.get("errorMessage"))
    rec.check(
        "errorType names RuntimeError",
        True,
        "RuntimeError" in str(payload.get("errorType", "")),
    )
    return rec


def l_04(ctx):
    rec = RowRecord("L-04", "lambda")
    lam = ctx.clients["lambda"]
    missing = "emu-missing-%s" % ctx.suffix()
    try:
        lam.invoke(FunctionName=missing, InvocationType="RequestResponse", Payload=b"{}")
        rec.check("missing function fails", "ClientError", "no error")
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code")
        status = exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
        rec.check("error code", "ResourceNotFoundException", code)
        rec.check("http status", 404, status)
    except Exception as exc:
        if looks_unsupported(exc):
            rec.mark_unsupported("%s: %s" % (type(exc).__name__, exc))
        else:
            raise
    return rec


def l_05(ctx):
    rec = RowRecord("L-05", "lambda")
    lam = ctx.clients["lambda"]
    try:
        lam.create_function(
            FunctionName="emu-%s" % ctx.suffix(),
            Runtime="python2.7-removed-runtime",
            Role=ctx.role_arn,
            Handler="lambda_function.ok_handler",
            Code={"ZipFile": _zip_bytes()},
        )
        rec.check("invalid runtime rejected", "ClientError", "no error")
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code")
        rec.check("error code", "InvalidParameterValueException", code)
    return rec


def l_06(ctx):
    rec = RowRecord("L-06", "lambda")
    lam = ctx.clients["lambda"]
    name, _ = _create(ctx, "lambda_function.ok_handler")
    try:
        lam.put_function_concurrency(
            FunctionName=name, ReservedConcurrentExecutions=3
        )
    except Exception as exc:
        if looks_unsupported(exc):
            rec.mark_unsupported("%s: %s" % (type(exc).__name__, exc))
            return rec
        raise
    got = lam.get_function(FunctionName=name)
    concurrency = (got.get("Concurrency") or {}).get("ReservedConcurrentExecutions")
    rec.check("reserved concurrency", 3, concurrency)
    return rec


def l_07(ctx):
    rec = RowRecord("L-07", "lambda")
    lam = ctx.clients["lambda"]
    name, _ = _create(ctx, "lambda_function.ok_handler")
    lam.delete_function(FunctionName=name)
    try:
        lam.get_function(FunctionName=name)
        rec.check("get after delete fails", "ClientError", "no error")
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code")
        rec.check("error code", "ResourceNotFoundException", code)
    names = [
        f["FunctionName"]
        for f in lam.list_functions().get("Functions", [])
    ]
    rec.check("absent from list_functions", False, name in names)
    return rec


ROWS = [l_01, l_02, l_03, l_04, l_05, l_06, l_07]
