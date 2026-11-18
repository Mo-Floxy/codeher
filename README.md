# CodeHer

**Code Your Future. Own Your Power.**

A learning and community platform for girls and women in technology: structured
curriculum, coding challenges run in an isolated sandbox, a project and Q&A
community, mentorship matching, XP-driven gamification and a database-backed
admin console.

Three independent processes, no duplicated implementations:

| Process   | Technology                             | Default address        |
| --------- | -------------------------------------- | ---------------------- |
| Frontend  | React 19 + Vite, Framer Motion, Recharts | http://127.0.0.1:5173 |
| Backend   | Django 5.2 LTS + Django REST Framework, MySQL | http://127.0.0.1:8000 |
| Runner    | Node.js sandbox service                 | http://127.0.0.1:8090  |

The backend is the only writer of application data. The frontend never talks to
the runner; Django proxies submissions to it over HTTP with a shared secret, so
user code never executes inside the web process.

---

## Repository layout

```
codeher/
  frontend/            React + Vite single-page app
    src/components/    buttons, cards, forms, editor, charts…
    src/layouts/       public shell, app shell, sidebar, footer
    src/pages/         public / auth / learning / challenges / community /
                       mentorship / app / admin
    src/features/      page-specific composition blocks
    src/hooks/         useAuth, useAsync, useToast, useMediaQuery…
    src/services/      api client, endpoints, formatters
    src/context/       auth + toast providers
    src/styles/        design tokens, dark theme, glassmorphism
  backend/             Django project
    config/            settings, root URLconf, test settings
    apps/users/        accounts, roles, profiles, follow graph
    apps/courses/      paths, courses, modules, lessons, quizzes
    apps/progress/     enrollments, completions, streaks, certificates, dashboard
    apps/challenges/   challenges, test cases, submissions, leaderboard
    apps/community/    posts, comments, projects, engagement, reports
    apps/mentorship/   mentor profiles, requests, sessions
    apps/achievements/ XP, levels, badges, activity, rankings
    apps/notifications/ in-app notifications
    apps/core/         shared models, admin API, permissions, seed data
    scripts/           api_smoke.py, audit_seed_tests.py
    setup.sql          MySQL database and user
    manage.py, requirements.txt, .env.example
  runner/              isolated execution service (lib/, server.js, smoke-test.js)
```

---

## Prerequisites

- **Python 3.12 or newer** (developed on 3.14) — `python --version`
- **Node.js 18 or newer** (developed on 23) — `node --version`
- **MySQL 8.0.11 or newer** — that is Django 5.2's floor for the MySQL backend — or a
  **TiDB Cloud Starter** cluster (TiDB self-reports as MySQL 8.0.11, which is inside the
  floor, so nothing in the code changes), or the SQLite fallback below
- Git for Windows

> On Windows, `python` in `PATH` is often the Microsoft Store alias that starts
> nothing. If a command below appears to do nothing, use the full interpreter
> path (for example `& "C:\Users\<you>\AppData\Local\Programs\Python\Python314\python.exe"`).

---

## Quick start

Open **three PowerShell windows**. Run the backend and the runner first; the
frontend works without them but shows honest "API unavailable" states. Every `cd`
below starts from the repository root — the folder that contains `backend\`,
`frontend\` and `runner\`.

### 1. Backend (terminal 1)

```powershell
cd backend

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

Copy-Item .env.example .env
notepad .env          # set DJANGO_SECRET_KEY, JWT_SIGNING_KEY, RUNNER_SHARED_SECRET, DB settings

python manage.py migrate
python manage.py seed
python manage.py runserver 127.0.0.1:8000
```

`manage.py seed` writes real rows for everything: 9 learning paths, 18 courses,
107 lessons, 33 quizzes, 12 challenges with graded test cases, community posts
and projects with genuine like/bookmark rows, mentor profiles, events and sample
learner progress produced through the actual completion services.

### 2. Sandbox runner (terminal 2)

```powershell
cd runner

npm install
Copy-Item .env.example .env
notepad .env          # RUNNER_SHARED_SECRET must match backend/.env, PYTHON_BIN must be a real interpreter

npm run start
npm run smoke         # optional: 17 self-checks against the live service
```

### 3. Frontend (terminal 3)

```powershell
cd frontend

npm install
Copy-Item .env.example .env
notepad .env          # optional: VITE_PROXY_TARGET, VITE_SOCIAL_* — the API base
                      # defaults to same-origin /api and vite.config.js proxies it

npm run dev           # http://127.0.0.1:5173
npm run build         # production bundle in dist/
npm run preview       # http://localhost:4173, same proxy, real bundle
```

The frontend never calls a hard-coded backend host: it requests `/api` and `/media`
on its own origin, and `vite.config.js` proxies those to Django (`npm run dev` and
`npm run preview`), while `frontend/public/_redirects` does the same in production. If
Django is not on `127.0.0.1:8000`, set `VITE_PROXY_TARGET`.

### No MySQL yet? Use SQLite

Everything above works unchanged with one extra environment setting, and the
automated tests already use it:

```powershell
$env:DB_ENGINE = "sqlite"
python manage.py migrate
python manage.py seed
```

This writes `backend/dev.sqlite3`. It is a development convenience, not the
deployment target — the spec's persistence requirement is MySQL.

---

## MySQL setup

1. Start MySQL and connect as an administrator:

   ```powershell
   & "C:\Program Files\MySQL\MySQL Server 9.7\bin\mysql.exe" -u root -p
   ```

2. Create the schema and application user. Open `backend/setup.sql`, replace
   both `REPLACE_WITH_A_STRONG_PASSWORD` occurrences with the same strong
   password, then run it from the `backend` directory:

   ```powershell
   & "C:\Program Files\MySQL\MySQL Server 9.7\bin\mysql.exe" -u root -p -e "source setup.sql"
   ```

3. Put that password in `backend/.env`:

   ```ini
   DB_ENGINE=mysql
   MYSQL_DATABASE=codeher
   MYSQL_USER=codeher_app
   MYSQL_PASSWORD=the-password-you-chose
   MYSQL_HOST=127.0.0.1
   MYSQL_PORT=3306
   ```

4. Migrate and seed as in step 1 of the quick start. Django never needs the
   root password — only the `codeher_app` credentials.

`requirements.txt` installs **PyMySQL**, so no MySQL C connector is required on
Windows. `config/settings.py` keeps every column on `utf8mb4` / `utf8mb4_unicode_ci`
so emoji and accents survive round-trips.

---

## Accounts

Sign in with the email address. The seed prints these when it finishes:

| Account               | Password                | Role    |
| --------------------- | ----------------------- | ------- |
| `ada@codeher.dev`     | `CodeHer!Learn2026`     | learner |
| `grace@codeher.dev`   | `CodeHer!Mentor2026`    | mentor  |
| `admin@codeher.dev`   | `CodeHer!Admin2026`     | admin   |
| `nia@`, `sofia@`, `omid@`, `mei@codeher.dev` | `CodeHer!Sample2026` | learners / mentor |

They are **demonstration accounts created by the seed command**, labelled as
such in the interface. Real members must register through `/signup`.

Because these passwords are in a public repository, `manage.py seed` refuses to
run against a database that is not on this machine — a stray `python manage.py
seed` with a TiDB `.env` would otherwise create a live admin login anyone reading
GitHub can use. `--force` overrides that for a disposable database you own. The
sign-in page only offers the one-click demo buttons in a development build;
`vite build` strips them.

### Creating your own administrator

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python manage.py createsuperuser
```

There are two admin surfaces:

- **`http://127.0.0.1:8000/django-admin/`** — Django's own admin, every model
  registered and editable. It is deliberately *not* at `/admin/`.
- **`http://127.0.0.1:5173/admin`** — the React admin console (metrics,
  charts, content management, moderation queue). Requires a member whose
  `role` is `admin`; `is_staff` alone is not enough for the API.

---

## What is implemented

**Interface** — dark glassmorphism design system, responsive sidebar for signed-in
members, Framer Motion transitions that stand down under `prefers-reduced-motion`,
and generated artwork instead of text placeholders: each course card paints the
learning path's own `color` and `icon` from the database (`src/components/CourseCover.jsx`),
and a member without an uploaded photo gets a deterministic gradient illustration
keyed to their account id (`Avatar` in `src/components/ui/Display.jsx`) — never a
drawn face and never initials.

**Public pages** — Home (hero, impact statistics, featured paths, how it works,
featured projects, mentorship, sample testimonials, final CTA), About, learning
catalog with search / level / category / path filters and sorting, course detail
with curriculum and enrollment.

**Accounts** — email-based registration with server-side password validation,
sign in / sign out, JWT access + refresh with rotation and blacklist on logout,
single-flight token refresh in the client, forgotten-password email and a reset
page, protected routes, role-based permissions (`learner`, `mentor`, `admin`),
profile editing with avatar upload and per-field public-visibility flags.

**Dashboard** — greeting, XP and level progress, enrolled courses, Continue
Learning with the real next lesson, completed lessons, streak tracker, weekly
activity chart, upcoming events, recommended courses, community activity,
achievements, quick links. A brand-new account sees zeros and empty states.

**Learning** — 9 paths, courses → modules → lessons → objectives, enrollment,
lesson player with prev/next, completion tracking, progress percentages,
bookmarks, server-graded quizzes with per-question feedback and explanations,
certificates with unique serials.

**Challenges** — 12 challenges in three difficulty groups with public and hidden
test cases, a CodeMirror editor with syntax highlighting, per-case feedback,
submission history, points, and a leaderboard built from real solves.
Execution happens in `runner/`, a separate localhost-only Node service:
JavaScript in a `node:vm` context, Python in a `-I -S` child process with a
stripped environment and an AST allowlist, both under CPU/memory/size limits.

**Community** — publish projects, share experiences, ask questions, threaded
comments, likes and bookmarks stored as `Engagement` rows, search by technology
and post type, follow members, report content, trending ranked by genuine
engagement, cursor-free paginated feeds.

**Mentorship** — mentor profiles with expertise and availability, request form,
status tracking (pending → accepted/declined), session scheduling with meeting
links, notifications, and role checks so only approved mentors appear in the
directory.

**Gamification** — XP from verified actions only (lesson, quiz pass, course,
first challenge solve, project publish, mentor match), levels from thresholds,
daily/weekly goals, streaks with longest-record retention, 19 badges evaluated
from stored rows, achievements page and leaderboard. Duplicate rewards are
impossible: `PointEvent(user, source_type, source_id, reason)` is unique at the
schema level.

**Notifications** — comments, replies, follows, mentorship updates, course
announcements, challenge results and achievement unlocks, unread count, mark one
or all as read, history.

**Admin console** — database-derived counters, sign-up/enrollment/engagement
analytics charts, member management (role, activation), course, lesson, path,
challenge and mentor editors, community moderation with the report queue,
announcement and notification management. Every table paginates and every
destructive action asks for confirmation.

**Quality** — loading, empty, error and success states everywhere; 404 and
error pages; responsive sidebar and mobile menu; keyboard-navigable dialogs;
visible focus rings; `prefers-reduced-motion` disables animation; semantic HTML
and labelled controls.

---

## API surface

All endpoints are under `/api/`. `GET /api/` returns a browsable index.

| Prefix                    | Purpose                                              |
| ------------------------- | ---------------------------------------------------- |
| `/api/auth/`              | register, login, logout, token refresh, password reset, me |
| `/api/users/`             | profiles, badges, follow, member directory, admin role edits |
| `/api/learning/`          | paths, courses, curriculum, lessons, enrollments, quizzes, certificates |
| `/api/progress/`          | summary, activity, bookmarks                         |
| `/api/dashboard/`         | the learner dashboard aggregate                      |
| `/api/challenges/`        | challenge list/detail, submissions, leaderboard      |
| `/api/community/`         | posts, comments, engagement, projects, reports       |
| `/api/mentorship/`        | mentors, requests, sessions                          |
| `/api/achievements/`      | badges, awards, rankings                             |
| `/api/notifications/`     | list, unread count, mark read                        |
| `/api/admin/`             | overview, analytics and content management (admin only) |
| `/api/site/`              | public impact statistics, testimonials, events        |
| `/api/uploads/`           | avatar and thumbnail uploads                         |

Consistent pagination (`{ count, next, previous, results }`), meaningful status
codes (`201` created, `205` signed out, `403` permitted-but-refused, `404`
absent), and field-level validation errors.

---

## Testing

```powershell
# Backend unit and API tests — always on SQLite
cd backend
.\.venv\Scripts\Activate.ps1
python -m pytest

# Fail if any constraint would be silently skipped on MySQL/TiDB
python scripts\check_mysql_compatibility.py

# Report misconfigured deployment variables — names only, never values
python scripts\check_deployment_env.py --dotenv .env

# Runner self-checks (the runner must be running)
cd ..\runner
npm run smoke

# Frontend unit tests and production build
cd ..\frontend
npm run test
npm run build

# End-to-end API walkthrough against a live backend
cd ..\backend
$env:DB_ENGINE = "sqlite"
python manage.py runserver 127.0.0.1:8000
# then, in another window:
.\.venv\Scripts\python.exe scripts\api_smoke.py      # 44 checks
.\.venv\Scripts\python.exe scripts\audit_seed_tests.py  # grades all seeded challenges
```

`audit_seed_tests.py` runs every seeded challenge's reference solution through
the live runner, so a test case that cannot actually pass is caught rather than
shipped.

Manual journey to verify by hand: sign up → browse the catalog → enroll →
finish a lesson (XP toast) → pass its quiz → solve a challenge → publish a
project → like and comment on a post → request a mentor → check the dashboard,
achievements, notifications and the admin console.

---

## Services that need your own configuration

Nothing here is faked. Until you configure them, the interface says so instead
of pretending:

- **Password-reset email** — set `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`,
  `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS` and switch `DJANGO_EMAIL_BACKEND` to
  the SMTP backend in `backend/.env`. In development the console backend prints
  the reset link, and the API returns it in the response body instead of
  silently claiming an email was sent.
- **Social / community links in the footer** — set `VITE_SOCIAL_GITHUB_URL`,
  `VITE_SOCIAL_LINKEDIN_URL`, `VITE_SOCIAL_COMMUNITY_URL`,
  `VITE_SOCIAL_FEED_URL` in `frontend/.env`. Unset entries render no icon, so
  the footer never links to somebody else's profile.
- **Hardened challenge execution** — `render.yaml` deploys `runner/` as its own
  service, which keeps learner code out of Django's process and answers only `POST
  /run` with the shared secret. That is isolation, not a jail: the bundled runner
  relies on `node:vm` and a Python subprocess with an AST allowlist, which a
  determined caller can probe. For real public traffic, put the same service behind
  Docker with `--network=none`, dropped capabilities and cgroup limits, or move it
  to Firecracker/gVisor, and keep `RUNNER_SHARED_SECRET` out of the repository.
  The `dev-runner-secret` default in `.env.example` is a placeholder — replace it on
  both services before deploying.
- **Avatar storage** — local `MEDIA_ROOT` by default. Point Django at object
  storage (`django-storages`) if you need shared storage across instances.

---

## Deploying on the free tier (TiDB Cloud + Render + Vercel)

`render.yaml` at the repository root defines both backend services, so Render
creates them from the blueprint instead of you clicking through two dashboards.
Everything below is the order that works; the only paid requirement is none.

### 1. TiDB Cloud Starter (the database)

TiDB speaks the MySQL wire protocol, so Django uses its MySQL backend and no code changes
are needed — but the protocol is not the whole story. TiDB announces itself as
`8.0.11-TiDB-v…` for compatibility, and Django checks the database version it declares on
**every** connection. Django 6.1 raised the MySQL floor to 8.4, which puts TiDB below it:
the connection fails with `NotSupportedError` before the first query, so no migration, no
deploy log and no request ever reaches the cluster. The pin in
`backend/requirements.txt` is therefore `Django>=5.2,<5.3` — 5.2's floor is exactly
8.0.11 and it is supported until April 2028. Raising that pin means raising the question
again, and CI's MySQL container is pinned to the 8.0 image precisely so that this fails in
a workflow run rather than on a deploy.

1. Create a **Starter** cluster in the TiDB Cloud console and note the four values
   from the *Connect* panel: the host string, **port 4000** (not 3306 — Serverless
   listens on 4000), the username and the database name. The username is not the
   short one you picked; it is the cluster's own identifier, shaped like
   `AbCdEf123.root` or `user%cluster-id`, and copying the wrong form fails
   authentication in a way that looks like a bad password.
2. Confirm the version the cluster declares by running `SELECT VERSION();` in the
   SQL editor. It reports something like `8.0.11-TiDB-v7.1.5`, and that banner is
   what decides which Django versions can connect at all — see the note above.
3. Set the network allowlist (**Connect → Public**) to include `0.0.0.0/0`, or
   whichever addresses your client actually comes from. Render's free tier has no
   fixed outbound IPs — that is a paid feature — so a restricted allowlist rejects
   every deployed request with a *timeout*, which reads exactly like a wrong port
   or a firewalled host. This is also why the password is the only thing standing
   between the internet and your data, and why it never belongs in chat.
4. Do not hunt for a CA bundle. TiDB Cloud Starter/Essential serves a **Let's
   Encrypt** certificate rather than a cluster-specific one, and PyMySQL checks it
   against the operating system trust store — which Render's Ubuntu image and your
   Windows machine both already contain. `MYSQL_SSL_CA` exists only for pinning a
   bundle of your own, and the deployed service no longer asks for it.
   The one setting that does matter is the opposite: never set
   `MYSQL_SSL_CHECK_HOSTNAME=false`. The driver then still encrypts but accepts any
   certificate, so someone on the path can terminate the TLS and read the password.
   Measured against a live gateway, the default gives
   `check_hostname=True, verify_mode=CERT_REQUIRED` and reaches authentication,
   while that flag gives `CERT_NONE`.
5. Create the schema and app user with `backend/setup.sql`, or let Django's
   migrations create the tables and use the cluster's admin user for the first
   deploy.
6. Never paste the database password into a chat, an issue, or a commit. Put it
   in `backend/.env` locally, and in Render's environment-variable form for the
   deployed service — `render.yaml` marks those keys `sync: false`, which means
   Render asks you for them rather than reading a committed value. If a password
   ever does get into a conversation or a log, rotate it in the console; nothing
   else needs to change.

### 2. Render (API + runner)

1. Push this repository to GitHub, then **New → Blueprint** and pick it. Render
   reads `render.yaml` and offers `codeher-api` (Python) and `codeher-runner`
   (Node).
2. Fill in the secret values it asks for: `DJANGO_SECRET_KEY`,
   `JWT_SIGNING_KEY`, `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`,
   `RUNNER_BASE_URL`, `RUNNER_SHARED_SECRET`, and the `EMAIL_*`
   keys if you want password-reset mail to actually send.
3. `RUNNER_SHARED_SECRET` must be identical on both services, and
   `RUNNER_BASE_URL` must be the runner's own `https://…onrender.com` URL, or
   every challenge submission answers 401.
4. Replace the placeholder hostnames in `render.yaml` and
   `frontend/public/_redirects` with the real ones once you have them.
   `DJANGO_ALLOWED_HOSTS` is the forgiving one: Render injects
   `RENDER_EXTERNAL_HOSTNAME` and settings.py trusts it, so a renamed service still
   answers. The CORS and `FRONTEND_ORIGIN` values are not guessed for you — a wrong
   one lets the page load and refuse every API call.
5. Both services deploy to **Frankfurt**, deliberately: the cluster is in
   `eu-central-1` and the free tier keeps no pooled connection, so each request
   opens a new one. Render cannot change a service's region after creation.
6. Migrations run inside `buildCommand` — Render's separate *pre-deploy* command
   is a paid feature, and the build environment can reach TiDB because it is an
   external host.
7. If the 0003 integrity migrations stop with a list of duplicate ids, that is
   the guard doing its job: it will not delete rows to make an index fit. Review
   the duplicates, then set `CODEHER_ALLOW_DEDUPE=1` for one deploy.
8. Before that first deploy, run
   `python scripts\check_deployment_env.py --dotenv .env` (or the same
   command with no flag inside Render's shell) to see which variables are
   missing, still placeholders, or quietly using a development default. It
   reports names and never values, so its output is safe to paste into an
   issue. This is the check that catches a blueprint that deploys green and
   then answers 400 to every request because `DJANGO_ALLOWED_HOSTS` is still
   `127.0.0.1`, or whose runner accepts code from anyone because
   `RUNNER_SHARED_SECRET` was never set.

The free instance's filesystem is wiped on every deploy, so uploaded avatars and
screenshots do not survive unless you attach a disk and set
`SERVE_MEDIA_IN_PRODUCTION=1`; with no disk, leave it off and accept that the
media rows outlive their files. Object storage is the real fix.

### 3. Vercel (frontend)

1. Import the repo. Vercel sees `backend`, `frontend` and `runner` as three
   separate applications and marks one of them for you, so check that **Root
   Directory** reads `frontend` before continuing: accepting its first offer
   silently creates a *Django* project that cannot build here. Framework
   detection and `vercel.json` then handle `npm run build` and the `dist` output.
2. Leave `VITE_API_BASE_URL` unset. `frontend/public/_redirects` proxies `/api` and
   `/media` to the Render host, which keeps the browser same-origin so no CORS
   configuration is needed and the SPA deep links (`/dashboard`, `/community/…`)
   resolve instead of 404ing.
   Use that file, not `vercel.json` `rewrites`. The first deploy of this project
   proved why: Vercel honored `buildCommand`, `outputDirectory`, `cleanUrls` and
   the `headers` block of `vercel.json`, but dropped the entire `rewrites` array
   without a build warning, so every deep link answered Vercel's own `NOT_FOUND`
   (`X-Vercel-Error`, `Server: Vercel`) instead of reaching Render. A file inside
   `public/` is copied into `dist/` by Vite and read per-deployment, which is why
   it survives that difference. `npm run build` followed by `cat dist/_redirects`
   is the check that it actually shipped.
3. Name the project **`codeher-frontend`** if the name is free, otherwise accept the
   suffix Vercel gives you and copy the real URL into `render.yaml`: this deployment
   came out as `https://codeher-tasz.vercel.app`, which is what `CORS_ALLOWED_ORIGINS`,
   `DJANGO_CSRF_TRUSTED_ORIGINS` and `FRONTEND_ORIGIN` now list. A wrong one lets the
   page load and refuse every API call. Note that `curl` cannot tell you which name is
   free: Vercel answers 404 both for an unclaimed subdomain and for one that does
   not exist, so only the URL it assigns after the deploy is evidence. Renaming the
   project later changes the `*.vercel.app` domain, so it must be followed by the same
   three edits.
4. Update the two `destination` hosts in `frontend/public/_redirects` to your real
   Render host if it differs from `codeher-api.onrender.com`.
5. Prefer a direct cross-origin call instead? Set `VITE_API_BASE_URL` to
   `https://<service>.onrender.com/api` and add
   `https://<project>.vercel.app` to `CORS_ALLOWED_ORIGINS` and
   `DJANGO_CSRF_TRUSTED_ORIGINS`.

### 4. After the first deploy

```bash
# one admin account, created against the live database
python manage.py createsuperuser          # with MYSQL_* pointing at TiDB
curl https://<service>.onrender.com/api/health/   # {"status":"ok","database":"up"}
node runner/smoke-test.js                        # against the deployed runner
```

Then delete or rotate the seeded demo accounts — they share one password.

### What the free tier costs you in feel

Render's free web services sleep after idle and take 30–60s to wake; the first
request after that is a cold start. `CONN_HEALTH_CHECKS` and the connect/read/
write timeouts in `settings.py` turn a dropped serverless connection into a
reconnect rather than a 500, but nothing can make the wake-up instant.

---

## Known limitations

- MySQL and TiDB cannot create a conditional unique index, so the rules that
  need one ("one like per user per target", "one open report per target", "one
  live mentorship request per pair", "one notification per dedupe key") are
  enforced by STORED generated columns plus plain unique indexes — see the
  `0003_db_enforced_*` migrations and `backend/scripts/check_mysql_compatibility.py`,
  which fails when a constraint would be silently skipped. SQLite and
  MySQL/TiDB therefore enforce the same rule in the schema rather than only in
  Python.
- The three `CheckConstraint`s (`users.Follow.no_self_follow`,
  `community.Engagement.exactly_one_engagement_target`,
  `mentorship.MentorshipRequest.no_self_mentorship`) are **not** created on TiDB. TiDB
  v6.3+ does enforce CHECK rules, but Django only emits them to a server claiming 8.0.16
  or newer and TiDB's compatibility banner says 8.0.11, so the DDL is skipped. The same
  rules are enforced in application code, which is what held them before the schema work;
  `backend/scripts/check_mysql_compatibility.py` reports them as a tolerated gap rather
  than failing, and the way to reclaim them is a `RunSQL` migration that adds each CHECK
  explicitly, which bypasses the version gate.
- The runner's isolation is deliberate but not a production jail (see above).
  Python submissions need `PYTHON_BIN` pointing at a real interpreter; the
  Windows Store alias will make every submission time out.
- Testimonials are seed content clearly labelled as samples, and impact
  statistics read from `/api/site/stats/` — if the API is unreachable the home
  page shows a "live stats unavailable" band rather than invented numbers.
- `npm run lint` uses oxlint and reports style warnings that were not part of
  this build's scope.
- Seeded demo accounts share one password on purpose so the demo is usable;
  rotate or delete them before any real deployment.

---

## Security notes

- Passwords use Django's PBKDF2 hashers; plaintext is never stored or logged.
- Secrets live in `backend/.env` (git-ignored) and are never mirrored into the
  frontend bundle — only `VITE_`-prefixed public values reach the browser.
- JWT refresh tokens rotate and are blacklisted on logout.
- SQL is generated by the ORM; user code is executed only in the runner.
- `POST /api/uploads/` requires a token, caps the file at 4 MB, maps an allowlist
  of image content types onto a fixed extension, ignores the filename you send in
  favour of a UUID name, and clamps the `folder` field to four known values — so it
  is not a path-traversal or stored-XSS surface. It does not decode the image,
  which is why `SECURE_CONTENT_TYPE_NOSNIFF` (on whenever `DEBUG` is off) matters;
  the `avatar`, `screenshot` and `thumbnail` model fields are `ImageField`s, so
  anything saved through them is validated as a real image as well.
- Admin endpoints check the `admin` role server-side, and content visibility
  flags are applied in serializers rather than only in markup.
- `DEFAULT_PERMISSION_CLASSES` is `AllowAny`, so protection is opt-in per view —
  that is a deliberate trade for having public pages, and it is enforced by
  `apps/core/tests/test_permissions.py`, which fails if any view in any installed
  app stops declaring its own gate or gains a write method that anonymous users
  can reach. Adding a view therefore cannot quietly become an open endpoint.
