# Role change during a browser login

Most applications log their users in through the browser: the login page,
a redirect back with a code, and the exchange of the code for tokens. This
recipe puts a change of role in the middle of that flow, between the
redirect and the exchange, and shows which role the token carries.

A
[stateful scenario](https://cdelmonte-zg.github.io/nanoidp/guides/stateful-scenarios.html)
creates the user and changes her role on the event
`authorization_completed`, which NanoIDP emits once the authorization code
is stored.

## Run it

From the repository root, with the requirements installed:

```bash
pytest -v recipes/role-change-during-browser-login
```

## What happens

| Step | Who | Result |
|---|---|---|
| 1 | the test arms `scenario.json` | carol exists with the role `USER` |
| 2 | the browser opens `/authorize` (code flow, PKCE) | the login page |
| 3 | the browser submits carol's password | a redirect to the application with a code; NanoIDP then changes carol's role to `ADMIN` |
| 4 | the application exchanges the code at `/token` | the token carries `ROLE_ADMIN` |
| 5 | the test removes the scenario | carol is gone |

The token carries the role carol has when the token is built, not the one
she had at the login page: the code names the user, it does not freeze her
roles.

## The files

- `scenario.json` is the declaration, as it is sent to
  `POST /api/runtime/scenarios`.
- `test_browser_login.py` plays both parts with `requests`: a session with
  its cookie for the browser, a plain call for the application. The
  redirect URI is never called; the test reads the code from the `Location`
  header.

## Use it in your project

- To test a real application, let a browser driver do steps 2 and 3 against
  your application's login link, and assert on what the application shows
  after the redirect.
- To change the user after the tokens exist instead, use the event
  `token_issued` with `grant_type: authorization_code`.
- The client is `demo-client`, which `nanoidp init` declares without
  `redirect_uris`: such a client accepts any absolute redirect URI. With
  your own configuration, use a client whose `redirect_uris` name your
  callback.
