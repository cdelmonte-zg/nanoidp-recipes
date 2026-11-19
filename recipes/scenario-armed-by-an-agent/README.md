# Scenario armed by an agent

The other recipes arm their scenario with a call to the runtime API. An
agent that tests an application has no HTTP client for that: it has tools.
This recipe arms, reads and removes the scenario of
[role-change-on-refresh](../role-change-on-refresh/) through the tools of
`nanoidp-mcp`, the MCP server that ships with NanoIDP.

The MCP server is a second process. It sees the scenarios of the running
server because both use one
[shared runtime store](https://cdelmonte-zg.github.io/nanoidp/guides/shared-runtime-store.html),
a SQLite file.

## Run it

From the repository root, with the requirements installed:

```bash
pytest -v recipes/scenario-armed-by-an-agent
```

This recipe always starts its own NanoIDP, also when `NANOIDP_URL` is set:
the MCP server needs the configuration directory of the instance.

## What happens

| Step | Who | Result |
|---|---|---|
| 1 | the fixture starts NanoIDP with `runtime.store: sqlite` | one store for every process on this configuration |
| 2 | the test starts `nanoidp-mcp` over stdio, as an agent's host does | the tools are available |
| 3 | the agent calls `arm_scenario` with `scenario.json` | frank exists with the role `USER` |
| 4 | the application logs in and refreshes, over HTTP | `ROLE_USER`, then `ROLE_ADMIN` |
| 5 | the agent calls `get_scenario` | the step is `applied`, seen once |
| 6 | the agent calls `remove_scenario` | frank is gone |

The MCP server arms, reads and removes; the step is fired by the server
that answers the application's request.

## The files

- `scenario.json` is the declaration; the arguments of `arm_scenario` are
  the same object the runtime API takes.
- `test_armed_by_an_agent.py` uses the MCP client of the `mcp` package in
  place of an agent.
- The `shared_idp` fixture in the root `conftest.py` adds the `runtime`
  block to the configuration `nanoidp init` writes.

## Use it in your project

- Give your agent's host the same configuration directory the server runs
  with (`NANOIDP_CONFIG_DIR`), and the same working directory when the keys
  directory is relative.
- Without a shared store the tools refuse with
  `MCP_RUNTIME_STORE_NOT_SHARED` and nothing is armed.
- Keep `runtime.path` outside the configuration directory, as here.
