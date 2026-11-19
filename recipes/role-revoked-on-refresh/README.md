# Role revoked on refresh

A user who loses a role has to lose what the role allowed, at the latest
when the application refreshes its token. A missed case shows no error:
the application keeps working, and still allows what the role allowed.

A
[stateful scenario](https://cdelmonte-zg.github.io/nanoidp/guides/stateful-scenarios.html)
creates the user with two roles and takes one away when the first token is
issued. The application's login and refresh drive it.

## Run it

From the repository root, with the requirements installed:

```bash
pytest -v recipes/role-revoked-on-refresh
```

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

## Use it in your project

- Keep the fixture and `scenario.json`; replace the requests with your
  application's login and refresh, and assert that the application refuses
  what `ADMIN` allowed once it holds the refreshed token.
- `update_user.roles` replaces the list whole: name the roles the user
  keeps, not the one that goes.
- The scenario owns its user. Do not declare a user of the same name in
  `users.yaml`: NanoIDP refuses the scenario with 409.
