"""The no-real-AWS guard, exercised as code."""

import re

import pytest
from botocore.exceptions import ClientError  # noqa: F401  (import surface check)

from src.factory import (
    PLACEHOLDER_ACCESS_KEY,
    PLACEHOLDER_ROLE_ARN,
    PLACEHOLDER_SECRET_KEY,
    EmulationServer,
    assert_local_endpoint,
    make_clients,
    make_session,
)

REAL_KEY_PATTERN = re.compile(r"^(AKIA|ASIA)[0-9A-Z]{16}$")


def test_placeholders_are_obviously_fake():
    assert PLACEHOLDER_ACCESS_KEY == "placeholder-access-key"
    assert PLACEHOLDER_SECRET_KEY == "placeholder-secret-key"
    assert not REAL_KEY_PATTERN.match(PLACEHOLDER_ACCESS_KEY)
    assert "placeholder" in PLACEHOLDER_ROLE_ARN


def test_factory_clients_point_at_loopback():
    with EmulationServer() as server:
        assert server.endpoint_url.startswith("http://127.0.0.1:")
        clients = make_clients(make_session(), server.endpoint_url)
        for client in clients.values():
            assert "127.0.0.1" in client.meta.endpoint_url


def test_guard_rejects_a_remote_endpoint():
    session = make_session()
    remote = session.client("s3", endpoint_url="https://example.com")
    with pytest.raises(AssertionError):
        assert_local_endpoint(remote)
