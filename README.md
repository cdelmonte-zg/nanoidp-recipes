# NanoIDP recipes

Runnable recipes for [NanoIDP](https://github.com/cdelmonte-zg/nanoidp), a
test identity provider. Each recipe is a small test that starts from a clean
NanoIDP, sets up one situation an application has to handle, and checks what
the application would see. Copy a recipe into your own test suite and replace
the requests with your application's.

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

## Recipes

| Recipe | What it shows |
|---|---|
| [role-change-on-refresh](recipes/role-change-on-refresh/) | A user's role changes between the login and the refresh; the refreshed token carries the new role |

## Requirements

Python 3.10 or later. The scenario recipes need NanoIDP 3.6.0 or later;
until that release is published, `requirements.txt` installs NanoIDP from its
main branch.

## Layout

```text
conftest.py        the idp fixture: one NanoIDP for the test session
recipes/<name>/    one recipe: a README, its declaration, its test
```
