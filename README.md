# NanoIDP recipes

Runnable recipes for [NanoIDP](https://github.com/cdelmonte-zg/nanoidp), a
test identity provider. Each recipe is a small test that starts from a clean
NanoIDP, sets up one situation an application has to handle, and checks what
the application would see.

To take one into your own project, start from
[role-revoked-on-refresh](recipes/role-revoked-on-refresh/): that folder runs
on its own, with its NanoIDP configuration and the fixture that starts
NanoIDP, and its README says what to change. The other recipes run inside
this catalogue and show what else a scenario can do.

## Run them

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
pytest -v
```

No NanoIDP has to be running. The test session starts one on a free port,
from the configuration `nanoidp init` writes into a temporary directory, and
stops it at the end. To use an instance you started yourself:

```bash
NANOIDP_URL=http://localhost:8000 pytest -v
```

Two recipes always start an instance of their own: scenario-armed-by-an-agent,
and role-revoked-on-refresh unless the instance `NANOIDP_URL` names declares
the client of its `settings.yaml`. To run the others against your instance,
name them: `pytest recipes/role-change-on-refresh`.

## Recipes

| Recipe | What it shows |
|---|---|
| [role-change-on-refresh](recipes/role-change-on-refresh/) | A user's role changes between the login and the refresh; the refreshed token carries the new role |
| [role-revoked-on-refresh](recipes/role-revoked-on-refresh/) | A user loses a role between the login and the refresh; the refreshed token and `/userinfo` no longer carry it |
| [role-change-during-browser-login](recipes/role-change-during-browser-login/) | A role changes between the login page and the code exchange of an authorization code flow with PKCE |
| [entitlement-gone-after-refreshes](recipes/entitlement-gone-after-refreshes/) | An entitlement disappears after the second refresh, with a step that counts |
| [department-move-on-refresh](recipes/department-move-on-refresh/) | A user changes group and attributes together; the refreshed token carries both |
| [scenario-armed-by-an-agent](recipes/scenario-armed-by-an-agent/) | An agent arms, reads and removes a scenario through the MCP server, over a shared runtime store |

## Requirements

Python 3.10 or later. The scenario recipes need NanoIDP 3.6.0 or later;
until the final release, `requirements.txt` installs its release candidate
from PyPI.

## Layout

```text
conftest.py        the idp and shared_idp fixtures: the NanoIDP the recipes run against
recipes/<name>/    one recipe: a README, its declaration, its test
                   (role-revoked-on-refresh also its own conftest.py and configuration)
```
