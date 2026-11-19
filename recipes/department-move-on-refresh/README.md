# Department move on refresh

Roles are not the only thing an application reads from a token. A user who
moves to another department changes group and attributes together, and an
application that scopes data by department has to follow.

A
[stateful scenario](https://cdelmonte-zg.github.io/nanoidp/guides/stateful-scenarios.html)
creates the user in `sales` and moves her to `finance` when the first token
is issued. One step changes two fields.

## Run it

From the repository root, with the requirements installed:

```bash
pytest -v recipes/department-move-on-refresh
```

## What happens

| Step | Who | Result |
|---|---|---|
| 1 | the test arms `scenario.json` | erin exists in the group `sales`, with `department: sales` and `cost_center: S-100` |
| 2 | the application logs in (password grant) | the token carries `groups: ["sales"]`, `GROUP_SALES` and the sales attributes; NanoIDP then moves erin |
| 3 | the application refreshes | the token carries `groups: ["finance"]`, `GROUP_FINANCE`, `department: finance` and `cost_center: F-200` |
| 4 | the test removes the scenario | erin is gone |

Her role stays `USER` through the move: a field the step does not name is
left as it is.

## Use it in your project

- Keep the fixture and `scenario.json`; replace the requests with your
  application's login and refresh, and assert that the application shows
  the data of the new department only.
- `attributes` is replaced whole, like every field a step names. A step
  that sets only `department` would remove `cost_center`: name every
  attribute the user keeps.
- The group reaches the token twice, as `groups` and, in upper case with
  the configured prefix, in `authorities`. Assert on the one your
  application reads.
- The scenario owns its user. Do not declare a user of the same name in
  `users.yaml`: NanoIDP refuses the scenario with 409.
