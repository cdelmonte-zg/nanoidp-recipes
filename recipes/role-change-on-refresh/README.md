# Role change on refresh

An application that refreshes its tokens has to act on what the new token
says: a user who was promoted, or lost a role, since the login. This is
awkward to test by hand, because something has to change the user at the
right moment between two calls of the application.

Here NanoIDP does it. A
[stateful scenario](https://cdelmonte-zg.github.io/nanoidp/guides/stateful-scenarios.html)
creates the user and changes her role when the first token is issued. The
application's own two calls, a login and a refresh, drive it; nothing else
happens in between.

## Run it

From the repository root, with the requirements installed:

```bash
pytest -v recipes/role-change-on-refresh
```

## What happens

| Step | Who | Result |
|---|---|---|
| 1 | the test arms `scenario.json` | alice exists with the role `USER` |
| 2 | the application logs in (password grant) | the token carries `ROLE_USER`; NanoIDP then changes alice's role to `ADMIN` |
| 3 | the application refreshes | the token carries `ROLE_ADMIN` |
| 4 | the test removes the scenario | alice is gone |

The token that fires the step still carries the old role: the change applies
after that token is built. That is what makes the order reliable.

## The files

- `scenario.json` is the declaration, as it is sent to
  `POST /api/runtime/scenarios`.
- `test_role_change.py` arms it in a fixture, does the two calls and checks
  the two tokens.
- `settings.yaml` and `users.yaml` are the NanoIDP configuration the test
  starts: one confidential client, `my-app`, and no declared users.

## Use it in your project

- Keep the fixture and `scenario.json`; replace the two requests in the test
  with your application's login and refresh, and assert on what your
  application does with the new role.
- The scenario owns its user. Do not declare a user of the same name in
  `users.yaml`: NanoIDP refuses the scenario with 409.
- The step names `grant_type: password`. For an application that logs in
  through the browser, use `authorization_code`.
- NanoIDP gives every client the password and the refresh grant: the
  client in `settings.yaml` needs only its id and its secret.

## Take it into your project

Copy this folder and the `conftest.py` of the repository root into a
directory of your test suite; nothing else is needed. In `settings.yaml`
put your application's client, port and issuer; in the test, your
application's calls. The steps are spelled out in
[role-revoked-on-refresh](../role-revoked-on-refresh/#use-it-in-your-project),
which ships with its `conftest.py` inside.
