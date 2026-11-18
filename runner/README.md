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
[runner] javascript: child process + node:vm realm, stripped env, permission model on
[runner] python:     3.14.7 via C:\...\backend\.venv\Scripts\python.exe (subprocess -I -S, AST allowlist)
[runner] This service executes untrusted code. The shared secret is the only front door:
[runner] keep RUNNER_SHARED_SECRET long and random, and rotate it everywhere if it leaks.
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

`GET /health` — service banner, which sandbox layers are live (including whether
this runtime supports `--permission`), and the Python probe result.

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

**JavaScript** runs in a throwaway `node` child process per submission, and
inside that child a fresh `node:vm` context. Both layers are load-bearing:

- The context is created *empty* — a new realm already has `Math`, `JSON`, `Map`,
  `Date`, the primitive constructors and everything else standard — and nothing
  from the runner's realm is assigned into it. That distinction is the whole
  point: a value copied in from outside carries its host realm with it, so
  injecting `Object` or `Array`, or a `console` stub, or a test's arguments
  array, handed the submission a host `Function` constructor, which is one call
  away from `process`. `npm run smoke` asserts each of those paths.
- The child gets an environment containing no credentials (the database password,
  the JWT signing key and the shared secret stay in the parent), reads its job
  from stdin and writes its report to stdout, so it never needs filesystem write
  access. Where the runtime supports it (Node 20+) it also starts with
  `--permission --allow-fs-read=*`, which makes `child_process`, workers and
  every write a runtime-level `ERR_ACCESS_DENIED` rather than a coding mistake.
  `GET /health` reports whether that layer is live.

V8's script timeout still stops infinite loops; the parent's kill timer is the
backstop if the child itself stops answering.

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

- `node:vm` is documented by Node as *not* a security mechanism, so it is not
  treated as one. The realm is what stops an honest mistake from being an
  incident; the process boundary, the stripped environment and the permission
  model are what an actual escape lands in. A submission that breaks out of both
  can still read files the runner can read and can make network requests — Node's
  permission model does not cover outbound connections yet.
- Each JavaScript submission now pays for a Node cold start (tens of milliseconds
  on Linux, more on Render's 0.1 CPU instance). That is the price of the process
  boundary; the Python path has always cost more.
- Memory is capped per child process (`--max-old-space-size`, from
  `memory_limit_mb`), so one allocation-hungry submission can no longer disturb
  another's runner.
- On Windows there is no `rlimit`, so Python CPU and memory limits are enforced
  by the wall-clock kill and the process boundary rather than by the kernel.
- No per-user rate limiting here; that lives in Django's throttle layer.
- The runner trusts `RUNNER_SHARED_SECRET` and nothing else. Locally that means
  "Django is the only client on localhost"; as deployed, Render gives this service
  a public `onrender.com` URL, so the secret is the entire front door. Generate a
  long random value (`node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"`),
  put the same value in both services, and treat a leaked one as a code-execution
  compromise.

The upgrade path for a hardened setup is a stronger isolation layer — a Docker
or gVisor/Firecracker sandbox per execution, with network egress disabled, a
read-only filesystem, dropped capabilities and a cgroup memory ceiling. The
Django side does not change: it is already a single HTTP call with a shared
secret, so swapping the runner is a swap of this service only.

Until that swap happens, keep the runner as its own service — which it is on
Render. Learner code runs as that service's user, so the database password and
the JWT signing key must never be in *its* environment, only in the API's. That
separation, not the sandbox, is what limits the blast radius of a full escape.
