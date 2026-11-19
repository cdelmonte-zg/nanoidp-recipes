"""A user's role changes between the login and the refresh.

The scenario in scenario.json creates alice with the role USER and changes
her role to ADMIN once the first token of a password grant is issued. The
test then does what an application does, a login and a refresh, and touches
nothing in between: the first token carries ROLE_USER, the refreshed one
ROLE_ADMIN.
"""

import base64
import json
from pathlib import Path

import pytest
import requests

SCENARIO = json.loads(Path(__file__).with_name("scenario.json").read_text(encoding="utf-8"))
CLIENT = ("demo-client", "demo-secret")  # the client `nanoidp init` declares
TIMEOUT = 10  # seconds: a request to a stuck IdP fails instead of hanging


def claims(token):
    """The claims of a JWT, read without checking the signature: this test
    looks at what the IdP issued, it does not stand in for a resource server."""
    payload = token.split(".")[1]
    return json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))


@pytest.fixture
def scenario(idp):
    """Arm the scenario for one test and remove it afterwards, with its user."""
    url = f"{idp}/api/runtime/scenarios"
    armed = requests.post(url, json=SCENARIO, timeout=TIMEOUT)
    if armed.status_code == 404:
        pytest.fail("this NanoIDP has no /api/runtime/scenarios: scenarios need 3.6.0 or later")
    assert armed.status_code == 201, armed.text
    yield f"{url}/{SCENARIO['name']}"
    removed = requests.delete(f"{url}/{SCENARIO['name']}", timeout=TIMEOUT)
    assert removed.status_code == 200, removed.text


def test_the_refreshed_token_carries_the_new_role(idp, scenario):
    user = SCENARIO["given"]["user"]

    login = requests.post(f"{idp}/token", auth=CLIENT, timeout=TIMEOUT, data={
        "grant_type": "password",
        "username": user["username"], "password": user["password"],
    })
    assert login.status_code == 200, login.text
    assert claims(login.json()["access_token"])["authorities"] == ["ROLE_USER"]

    refresh = requests.post(f"{idp}/token", auth=CLIENT, timeout=TIMEOUT, data={
        "grant_type": "refresh_token",
        "refresh_token": login.json()["refresh_token"],
    })
    assert refresh.status_code == 200, refresh.text
    assert claims(refresh.json()["access_token"])["authorities"] == ["ROLE_ADMIN"]

    # The scenario says what it did: the step fired once and was applied
    step = requests.get(scenario, timeout=TIMEOUT).json()["steps"][0]
    assert (step["state"], step["seen"]) == ("applied", 1)
