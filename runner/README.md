# CodeHer runner

A tiny standalone HTTP service that executes learner code. Django never runs
submission code inside its own process — it POSTs to this service and reads back
a pass/fail report. If the runner is unreachable, the API answers **503** rather
than pretending the code passed.

## Start it

```powershell
cd codeher\runner
Copy-Item .env.example .env          # then edit RUNNER_SHARED_SECRET and PYTHON_BIN
npm install                          # no dependencies today, but keeps the lockfile honest
npm start
```

`npm start` runs `node --max-old-space-size=128 server.js`.

You should see:

```
[runner] listening on http://127.0.0.1:8090/run
[runner] javascript: node:vm (timeout + no require/process/fetch)
[runner] python:     3.14.7 via C:\...\backend\.venv\Scripts\python.exe (subprocess -I -S, AST allowlist)
[runner] NOT production-hardened. See README.md before exposing this beyond localhost.
```

`RUNNER_SHARED_SECRET` must match the value in `backend/.env`, and
`PYTHON_BIN` must be an absolute path to a real interpreter. On Windows a bare
`python` is usually the Microsoft Store alias, which starts nothing and makes
every Python submission hit the timeout; the startup probe tells you this in one
line instead of leaving you to guess.

## Configuration

| Variable | Default | Meaning |
| --- | --- | --- |
| `RUNNER_SHARED_SECRET` | required, refuses to boot without it | compared against the `X-Runner-Secret` header |
| `RUNNER_HOST` | `127.0.0.1` | bind address |
| `RUNNER_PORT` | `8090` | bind port |
| `PYTHON_BIN` | `python` | interpreter used for Python submissions |
| `RUNNER_MAX_CODE_BYTES` | `20000` | submissions larger than this are rejected |

Django reaches this service through `RUNNER_BASE_URL` in `backend/.env`, which
defaults to `http://127.0.0.1:8090`.

## Endpoints

`GET /health` — service banner plus the Python probe result.

`POST /run` with `X-Runner-Secret` and:

```json
{
  "language": "javascript",
  "code": "function solution(text) { return text; }",
  "function_name": "solution",
  "time_limit_ms": 2000,
  "memory_limit_mb": 128,
  "tests": [{ "name": "echo", "args": ["hi"], "expected": "hi" }]
}
```

```json
{
  "ok": true,
  "runtime_ms": 3,
  "results": [{ "name": "echo", "passed": true, "expected": "hi", "actual": "hi", "error": "" }]
}
```

`401` bad secret · `400` malformed payload · `413` oversized body.

## How each language is confined

**JavaScript** runs as a `node:vm` `Script` inside a context object that only
contains safe globals (`Math`, `JSON`, `Map`, `Set`, `Date`, `RegExp`, the
primitive constructors). There is no `require`, `process`, `fetch` or
`console` output, so a submission cannot reach the filesystem, the network or
the runner's environment. V8's own script timeout stops infinite loops without
killing the service.

**Python** is validated before it is compiled: every AST node must be on an
allowlist, and `import`, `with`, `global`, `nonlocal`, `await`, async functions,
any name in a ban list (`open`, `exec`, `eval`, `compile`, `globals`, `getattr`,
`__import__`, …) and any attribute starting with `_` are rejected outright — so
`__class__.__mro__[1].__subclasses__()` never reaches the compiler. Execution
happens in a separate interpreter started with `-I -S` (isolated, no
site-packages), with a stripped environment, a working directory that is deleted
afterwards, and a hard kill when the time budget is exceeded.

## Known limitations — read before deploying

This is a **development and demonstration sandbox, not a production security
boundary**. Be honest about it in any write-up:

- `node:vm` is explicitly documented by Node as *not* a security mechanism. It
  stops accidents and casual escapes; a determined attacker with the ability to
  submit arbitrary JavaScript can still find ways out.
- Memory is capped for the whole Node process (`--max-old-space-size`), not per
  request. A submission that allocates aggressively can disturb other
  submissions.
- On Windows there is no `rlimit`, so Python CPU and memory limits are enforced
  by the wall-clock kill and the process boundary rather than by the kernel.
- No per-user rate limiting here; that lives in Django's throttle layer.
- The runner trusts that Django is the only client on localhost. Anything that
  can reach port 8090 and guess the shared secret can execute code as the user
  running the runner.

The upgrade path for real deployments is a stronger isolation layer — a Docker
or gVisor/Firecracker sandbox per execution, with network egress disabled, a
read-only filesystem, dropped capabilities and a cgroup memory ceiling. The
Django side does not change: it is already a single HTTP call with a shared
secret, so swapping the runner is a swap of this service only.

Until that swap happens, run the runner on localhost only, as a low-privilege
account, on a machine with nothing sensitive on it.
