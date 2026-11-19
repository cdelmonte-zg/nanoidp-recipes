"""An agent arms the scenario through the MCP server.

The same scenario as role-change-on-refresh, but nothing here calls the
runtime API: an MCP client starts `nanoidp-mcp` over stdio, as an agent's
host does, and uses the tools `arm_scenario`, `get_scenario` and
`remove_scenario`. The MCP server is a second process; it sees the server's
scenarios because both use one runtime store, a SQLite file.
"""

import asyncio
import base64
import json
import os
import sys
from pathlib import Path

import requests
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SCENARIO = json.loads(Path(__file__).with_name("scenario.json").read_text(encoding="utf-8"))
CLIENT = ("demo-client", "demo-secret")  # the client `nanoidp init` declares
TIMEOUT = 10  # seconds: a request to a stuck IdP fails instead of hanging


def claims(token):
    """The claims of a JWT, read without checking the signature: this test
    looks at what the IdP issued, it does not stand in for a resource server."""
    payload = token.split(".")[1]
    return json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))


def login_and_refresh(idp):
    """What the application does, over HTTP: the authorities of its two tokens."""
    user = SCENARIO["given"]["user"]
    login = requests.post(f"{idp}/token", auth=CLIENT, timeout=TIMEOUT, data={
        "grant_type": "password",
        "username": user["username"], "password": user["password"],
    })
    assert login.status_code == 200, login.text
    refresh = requests.post(f"{idp}/token", auth=CLIENT, timeout=TIMEOUT, data={
        "grant_type": "refresh_token",
        "refresh_token": login.json()["refresh_token"],
    })
    assert refresh.status_code == 200, refresh.text
    return [claims(answer.json()["access_token"])["authorities"] for answer in (login, refresh)]


def test_an_agent_arms_reads_and_removes_the_scenario(shared_idp):
    # The MCP server gets the configuration directory of the running server
    # and its working directory, so both processes use the same store and keys
    mcp_server = StdioServerParameters(
        command=sys.executable, args=["-m", "nanoidp.mcp_server"],
        env={**os.environ, "NANOIDP_CONFIG_DIR": str(shared_idp.config_dir)},
        cwd=str(shared_idp.home),
    )

    async def agent():
        async with stdio_client(mcp_server) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                async def call(tool, arguments):
                    answer = await session.call_tool(tool, arguments)
                    return json.loads(answer.content[0].text)

                armed = await call("arm_scenario", SCENARIO)
                assert armed.get("success") is True, armed
                try:
                    # The application's calls are answered by the HTTP server,
                    # which fires the step; the MCP server fires nothing
                    first, second = await asyncio.to_thread(login_and_refresh, shared_idp.url)
                    assert first == ["ROLE_USER"]
                    assert second == ["ROLE_ADMIN"]

                    read_back = await call("get_scenario", {"name": SCENARIO["name"]})
                    step = read_back["scenario"]["steps"][0]
                    assert (step["state"], step["seen"]) == ("applied", 1)
                finally:
                    removed = await call("remove_scenario", {"name": SCENARIO["name"]})
                assert removed.get("user_removed") is True, removed

    asyncio.run(agent())
