"""An entitlement disappears after the second refresh.

The scenario in scenario.json creates dave with the entitlement `reports`
and removes it once two tokens of a refresh grant are issued. The login and
the first two refreshes carry ENT_reports; the third refresh does not. A
step with a `count` puts the change at a later point of a session than its
first call.
"""

import base64
import json
from pathlib import Path

import pytest
import requests

SCENARIO = json.loads(Path(__file__).with_name("scenario.json").read_text(encoding="utf-8"))
CLIENT = ("my-app", "my-app-secret")  # the client settings.yaml declares
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


def test_the_third_refresh_no_longer_carries_the_entitlement(idp, scenario):
    user = SCENARIO["given"]["user"]

    def refresh(tokens):
        # Each refresh uses the refresh token of the answer before it
        answer = requests.post(f"{idp}/token", auth=CLIENT, timeout=TIMEOUT, data={
            "grant_type": "refresh_token", "refresh_token": tokens["refresh_token"],
        })
        assert answer.status_code == 200, answer.text
        return answer.json()

    def step():
        return requests.get(scenario, timeout=TIMEOUT).json()["steps"][0]

    login = requests.post(f"{idp}/token", auth=CLIENT, timeout=TIMEOUT, data={
        "grant_type": "password",
        "username": user["username"], "password": user["password"],
    })
    assert login.status_code == 200, login.text
    tokens = login.json()
    assert "ENT_reports" in claims(tokens["access_token"])["authorities"]
    assert step()["seen"] == 0  # the login is a password grant: it does not count

    tokens = refresh(tokens)
    assert "ENT_reports" in claims(tokens["access_token"])["authorities"]
    assert (step()["state"], step()["seen"]) == ("waiting", 1)

    tokens = refresh(tokens)  # the second refresh fires the step, with the old value
    assert "ENT_reports" in claims(tokens["access_token"])["authorities"]
    assert (step()["state"], step()["seen"]) == ("applied", 2)

    tokens = refresh(tokens)
    assert claims(tokens["access_token"])["authorities"] == ["ROLE_USER"]
