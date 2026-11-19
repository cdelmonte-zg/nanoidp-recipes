"""A user loses a role between the login and the refresh.

The scenario in scenario.json creates bob with the roles USER and ADMIN and
takes ADMIN away once the first token of a password grant is issued. The
token from the login still carries ROLE_ADMIN; the refreshed one does not,
and neither does /userinfo, even when asked with the token from the login.
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


def test_the_refreshed_token_no_longer_carries_the_role(idp, scenario):
    user = SCENARIO["given"]["user"]

    login = requests.post(f"{idp}/token", auth=CLIENT, timeout=TIMEOUT, data={
        "grant_type": "password",
        "username": user["username"], "password": user["password"],
    })
    assert login.status_code == 200, login.text
    old_token = login.json()["access_token"]
    assert "ROLE_ADMIN" in claims(old_token)["authorities"]

    refresh = requests.post(f"{idp}/token", auth=CLIENT, timeout=TIMEOUT, data={
        "grant_type": "refresh_token",
        "refresh_token": login.json()["refresh_token"],
    })
    assert refresh.status_code == 200, refresh.text
    assert claims(refresh.json()["access_token"])["authorities"] == ["ROLE_USER"]

    # The token from the login is still valid and still says ADMIN: that is
    # what a token is. /userinfo reads the user when asked, so it already
    # answers without the role, also for that token
    userinfo = requests.get(f"{idp}/userinfo", timeout=TIMEOUT,
                            headers={"Authorization": f"Bearer {old_token}"})
    assert userinfo.status_code == 200, userinfo.text
    assert userinfo.json()["roles"] == ["USER"]

    step = requests.get(scenario, timeout=TIMEOUT).json()["steps"][0]
    assert (step["state"], step["seen"]) == ("applied", 1)
