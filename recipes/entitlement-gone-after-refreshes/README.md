# Entitlement gone after two refreshes

A change does not always come right after the login. A subscription runs
out, an access is withdrawn in the middle of a session that has been
refreshing its token for a while. This recipe puts the change at a later
point: after the second refresh.

A
[stateful scenario](https://cdelmonte-zg.github.io/nanoidp/guides/stateful-scenarios.html)
creates the user with an entitlement and removes it with a step that has a
`count` and names the refresh grant, so the login does not count.

## Run it

From the repository root, with the requirements installed:

```bash
pytest -v recipes/entitlement-gone-after-refreshes
```

## What happens

| Step | Who | Token | The step has seen |
|---|---|---|---|
| 1 | the test arms `scenario.json` | | 0 |
| 2 | the application logs in (password grant) | `ENT_reports` | 0 |
| 3 | the application refreshes | `ENT_reports` | 1 |
| 4 | the application refreshes | `ENT_reports`; NanoIDP then removes the entitlement | 2, applied |
| 5 | the application refreshes | no `ENT_reports` | 2 |
| 6 | the test removes the scenario | | |

The refresh that reaches the count still carries the old value, as every
token that fires a step does. `GET /api/runtime/scenarios/{name}` answers
`seen` and `state` for each step, which the test reads between the calls.

## Use it in your project

- Keep the fixture and `scenario.json`; replace the requests with your
  application's session, and assert that it stops offering what the
  entitlement allowed after the refresh in step 5.
- Each refresh answers a new refresh token; the test uses it for the next
  call, as an application should.
- `count` counts the matching events since the scenario was armed, for each
  step on its own. Without `grant_type` the login would count too.
