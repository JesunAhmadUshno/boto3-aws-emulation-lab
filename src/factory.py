"""Client factory and server handle for the emulation study.

Every boto3 client in this study is created here. The factory forces
the endpoint to a moto server on 127.0.0.1 and uses dummy placeholder
credentials defined below (obviously fake strings, passed explicitly
at client creation inside the test process). No credential is read
from the environment or from instance metadata.
"""

import os

os.environ.setdefault("AWS_EC2_METADATA_DISABLED", "true")

import boto3
from botocore.config import Config
from moto.server import ThreadedMotoServer

# Dummy placeholders. These are not credentials for anything; they
# exist so boto3 will sign requests to the local emulator. They are
# deliberately not in any real credential format.
PLACEHOLDER_ACCESS_KEY = "placeholder-access-key"
PLACEHOLDER_SECRET_KEY = "placeholder-secret-key"
PLACEHOLDER_ROLE_ARN = "arn:aws:iam::123456789012:role/placeholder-role"
REGION = "us-east-1"

SERVICES = ("s3", "sqs", "lambda")


class EmulationServer:
    """One moto server on 127.0.0.1 with an ephemeral port."""

    def __init__(self):
        self._server = ThreadedMotoServer(
            ip_address="127.0.0.1", port=0, verbose=False
        )
        self.endpoint_url = None

    def __enter__(self):
        self._server.start()
        host, port = self._server.get_host_and_port()
        assert host == "127.0.0.1", host
        self.endpoint_url = "http://%s:%d" % (host, port)
        return self

    def __exit__(self, *exc):
        self._server.stop()
        return False


def make_session():
    return boto3.Session(
        aws_access_key_id=PLACEHOLDER_ACCESS_KEY,
        aws_secret_access_key=PLACEHOLDER_SECRET_KEY,
        region_name=REGION,
    )


def make_client(session, endpoint_url, service):
    """The only client constructor the study is allowed to use."""
    client = session.client(
        service,
        endpoint_url=endpoint_url,
        config=Config(retries={"max_attempts": 1}, max_pool_connections=25),
    )
    assert_local_endpoint(client)
    return client


def assert_local_endpoint(client):
    """Guard: no client may point anywhere but loopback."""
    host = client.meta.endpoint_url.split("://", 1)[1].split(":")[0].split("/")[0]
    assert host == "127.0.0.1", "client endpoint is not loopback: %s" % host


def make_clients(session, endpoint_url):
    clients = {svc: make_client(session, endpoint_url, svc) for svc in SERVICES}
    # IAM is setup machinery only (the Lambda execution role), never
    # a scored service in this study.
    clients["iam"] = make_client(session, endpoint_url, "iam")
    return clients


def ensure_execution_role(clients):
    """Create the Lambda execution role inside the emulator and
    return its ARN, the documented setup step before CreateFunction.
    See DECISIONS.md D3: the emulator validates that the role exists,
    exactly as AWS does, so a bare placeholder ARN cannot be used.
    """
    import json

    trust = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "lambda.amazonaws.com"},
                "Action": "sts:AssumeRole",
            }
        ],
    }
    resp = clients["iam"].create_role(
        RoleName="emulation-lab-role",
        AssumeRolePolicyDocument=json.dumps(trust),
    )
    return resp["Role"]["Arn"]
