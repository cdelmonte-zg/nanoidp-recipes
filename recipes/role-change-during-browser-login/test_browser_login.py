"""A user's role changes between the login page and the code exchange.

The scenario in scenario.json creates carol with the role USER and changes
her role to ADMIN once her authorization code is stored. The test drives an
authorization code flow with PKCE the way a browser and a single page
application do: the login page, the redirect with the code, the exchange at
/token. The token of the exchange carries ROLE_ADMIN: NanoIDP reads the user
when the token is built, not when the code was issued.
"""

import base64
import hashlib
import json
import secrets
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest
import requests

SCENARIO = json.loads(Path(__file__).with_name("scenario.json").read_text(encoding="utf-8"))
CLIENT_ID = "my-spa"  # the public client settings.yaml declares: no secret, PKCE
REDIRECT_URI = "http://localhost:3000/callback"  # registered in settings.yaml; never called
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


def test_the_token_of_the_code_carries_the_new_role(idp, scenario):
    user = SCENARIO["given"]["user"]
    verifier = secrets.token_urlsafe(32)
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    state = secrets.token_urlsafe(16)

    # The browser: the login page, then the form, which answers with the
    # redirect to the application. The session cookie ties the two together
    browser = requests.Session()
    page = browser.get(f"{idp}/authorize", allow_redirects=False, timeout=TIMEOUT, params={
        "response_type": "code", "client_id": CLIENT_ID, "redirect_uri": REDIRECT_URI,
        "scope": "openid", "state": state,
        "code_challenge": challenge, "code_challenge_method": "S256",
    })
    assert page.status_code == 200, page.text
    submitted = browser.post(f"{idp}/authorize", allow_redirects=False, timeout=TIMEOUT, data={
        "username": user["username"], "password": user["password"],
    })
    assert submitted.status_code == 302, submitted.text
    redirect = urlparse(submitted.headers["Location"])
    answer = parse_qs(redirect.query)
    assert submitted.headers["Location"].startswith(REDIRECT_URI) and answer["state"] == [state]

    # The code exists, so the step has fired: carol is an ADMIN from here on
    step = requests.get(scenario, timeout=TIMEOUT).json()["steps"][0]
    assert (step["state"], step["seen"]) == ("applied", 1)

    # The application: the code for a token. A public client names itself
    # and proves with the PKCE verifier that it is the one that asked
    exchange = requests.post(f"{idp}/token", timeout=TIMEOUT, data={
        "grant_type": "authorization_code", "code": answer["code"][0],
        "redirect_uri": REDIRECT_URI, "code_verifier": verifier,
        "client_id": CLIENT_ID,
    })
    assert exchange.status_code == 200, exchange.text
    assert claims(exchange.json()["access_token"])["authorities"] == ["ROLE_ADMIN"]
