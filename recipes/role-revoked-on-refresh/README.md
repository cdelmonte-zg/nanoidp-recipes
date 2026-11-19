# Role revoked on refresh

A user who loses a role has to lose what the role allowed, at the latest
when the application refreshes its token. A missed case shows no error:
the application keeps working, and still allows what the role allowed.

A
[stateful scenario](https://cdelmonte-zg.github.io/nanoidp/guides/stateful-scenarios.html)
creates the user with two roles and takes one away when the first token is
issued. The application's login and refresh drive it.

Every recipe of the catalogue has its own NanoIDP configuration. This one
also carries the fixture that starts NanoIDP, a copy of the `conftest.py`
of the repository root, so the folder alone can be downloaded and taken
into another project as it is.

## Take the recipe and run it

Download this folder from the tag `v2`, install what it needs, run the test:

```bash
curl -fsSL -o nanoidp-recipes.tar.gz \
  https://github.com/cdelmonte-zg/nanoidp-recipes/archive/refs/tags/v2.tar.gz
tar -xzf nanoidp-recipes.tar.gz --strip-components=2 \
  nanoidp-recipes-2/recipes/role-revoked-on-refresh
cd role-revoked-on-refresh
pip install "nanoidp>=3.6.0rc1" pytest requests pyyaml
pytest -v
```

Nothing has to be running. The test starts NanoIDP on port 8000 with
`settings.yaml` and `users.yaml`, and stops it at the end. Scenarios need
NanoIDP 3.6.0; until that release is final, the requirement above names its
release candidate.

## Only arm the scenario

For a NanoIDP that is already running with the client of `settings.yaml`,
when all you want is the scenario, to drive it by hand or from your own
tests:

```bash
curl -fsSL -o scenario.json \
  https://raw.githubusercontent.com/cdelmonte-zg/nanoidp-recipes/v2/recipes/role-revoked-on-refresh/scenario.json \
  && curl -sS --fail-with-body -X POST http://localhost:8000/api/runtime/scenarios \
       -H 'Content-Type: application/json' -d @scenario.json
```

The two failures stay apart, and both fail the command, so it can stand in
a script. When the download fails, the first `curl` says so and exits, and
nothing is sent to NanoIDP. When NanoIDP refuses the declaration, its
answer is printed, a JSON object with `error` and `kind`, for example for
a scenario or a user of that name that exists already, and the second
`curl` exits with 22. `--fail-with-body` needs curl 7.76 or later. Remove
the scenario and its user with
`curl -X DELETE http://localhost:8000/api/runtime/scenarios/role-revoked-on-refresh`.

## What happens

| Step | Who | Result |
|---|---|---|
| 1 | the test arms `scenario.json` | bob exists with the roles `USER` and `ADMIN` |
| 2 | the application logs in (password grant) | the token carries `ROLE_ADMIN`; NanoIDP then leaves bob with `USER` only |
| 3 | the application refreshes | the token carries `ROLE_USER` only |
| 4 | the application asks `/userinfo` with the token from step 2 | `roles` is `["USER"]` |
| 5 | the test removes the scenario | bob is gone |

The token from the login stays valid and keeps saying `ROLE_ADMIN` until it
expires: a signed token cannot be changed after it is issued. Step 4 shows
the way around it for an application that cannot wait for the refresh:
`/userinfo` reads the user when it is asked.

## The files

| File | What it is |
|---|---|
| `scenario.json` | the declaration, as it is sent to `POST /api/runtime/scenarios` |
| `test_role_revoked.py` | arms the scenario in a fixture, does the calls, checks the tokens |
| `conftest.py` | the `idp` fixture: starts NanoIDP with the two files below, or uses `NANOIDP_URL`; the same file as in the repository root |
| `settings.yaml` | one confidential client, `my-app`, and the port and issuer |
| `users.yaml` | no declared users: the scenario creates its own |

## Use it in your project

1. Copy the folder's files, README aside, into a directory of your test suite.
2. In `settings.yaml`, replace `my-app` and its secret with your
   application's client, and set `server.port` and `oauth.issuer` to the
   address your application reaches NanoIDP at. Use the same client in
   `CLIENT` at the top of the test.
3. In the test, replace the login and the refresh with your application's
   own. The comment `YOUR APPLICATION` marks where to assert that it
   refuses what `ADMIN` allowed once it holds the refreshed token.
4. In CI, the same as above: install, `pytest`, nothing else to start. If
   your pipeline already runs a NanoIDP with this configuration, set
   `NANOIDP_URL` to it and the fixture starts nothing.

Good to know:

- `update_user.roles` replaces the list whole: name the roles the user
  keeps, not the one that goes.
- The scenario owns its user. A user of the same name in `users.yaml`
  makes NanoIDP refuse the scenario with 409.
- With `session.management_secret` set in your configuration, arming and
  removing a scenario need it, as every write of `/api` does.
