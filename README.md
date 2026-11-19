# NanoIDP recipes

Runnable recipes for [NanoIDP](https://github.com/cdelmonte-zg/nanoidp), a
test identity provider. Each recipe is a small test that starts from a clean
NanoIDP, sets up one situation an application has to handle, and checks what
the application would see.

Every recipe has its own NanoIDP configuration, `settings.yaml` and
`users.yaml`, next to its declaration and its test: a different story needs
a different client, different users, a different store. A recipe folder and
the `conftest.py` of this directory are all a project needs to take one
away. Start from
[role-revoked-on-refresh](recipes/role-revoked-on-refresh/), which carries
its `conftest.py` inside, can be downloaded with one command, and says what
to change.

## Run them

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
pytest -v
```

No NanoIDP has to be running. Each recipe gets a NanoIDP of its own, started
with the recipe's configuration on the port its `settings.yaml` names (8000)
and stopped when the recipe is done. Port 8000 has to be free.

To run one recipe against an instance you started yourself with that
recipe's configuration:

```bash
NANOIDP_URL=http://localhost:8000 pytest -v recipes/role-change-on-refresh
```

## Recipes

| Recipe | What it shows |
|---|---|
| [role-change-on-refresh](recipes/role-change-on-refresh/) | A user's role changes between the login and the refresh; the refreshed token carries the new role |
| [role-revoked-on-refresh](recipes/role-revoked-on-refresh/) | A user loses a role between the login and the refresh; the refreshed token and `/userinfo` no longer carry it |
| [role-change-during-browser-login](recipes/role-change-during-browser-login/) | A role changes between the login page and the code exchange of an authorization code flow with PKCE |
| [entitlement-gone-after-refreshes](recipes/entitlement-gone-after-refreshes/) | An entitlement disappears after the second refresh, with a step that counts |
| [department-move-on-refresh](recipes/department-move-on-refresh/) | A user changes group and attributes together; the refreshed token carries both |
| [scenario-armed-by-an-agent](recipes/scenario-armed-by-an-agent/) | An agent arms, reads and removes a scenario through the MCP server, over a shared runtime store |

## Run by NanoIDP's own CI

NanoIDP runs these recipes on its pull requests, against the code of the
pull request, through `.github/workflows/run-recipes.yml` of this
repository pinned to a commit. A change there that breaks a recipe shows
as a check before it is merged.

## Requirements

Python 3.10 or later. The scenario recipes need NanoIDP 3.6.0 or later;
until the final release, `requirements.txt` installs its release candidate
from PyPI.

## Layout

```text
conftest.py        the idp fixture: starts the NanoIDP of the recipe under test
recipes/<name>/    one recipe:
  README.md          what it shows and how to adapt it
  scenario.json      the declaration
  settings.yaml      the NanoIDP configuration the recipe needs
  users.yaml         its declared users, often none
  test_*.py          the test
```

`recipes/role-revoked-on-refresh/conftest.py` is a copy of the root one, kept
identical by CI.
