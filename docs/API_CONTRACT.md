# CodeHer API Contract

Base URL: `http://127.0.0.1:8000/api`. All list responses are paginated DRF style:
`{ count, next, previous, results: [...] }` with `?page=&page_size=` (max 50).

Auth: `Authorization: Bearer <access>` (SimpleJWT). Refresh via cookie-free body.
Errors: DRF field errors `{ field: [messages ] }` or `{ detail: "..." }`. Status codes are meaningful
(201 create, 204 delete, 400 validation, 401 unauthenticated, 403 permission denied, 404 missing).

Roles live on `Profile.role`: `learner` | `mentor` | `admin`. `is_staff` is also set for admins.
`/api/admin/**` requires role `admin` or `is_staff`.

## auth
| Method | Path | Body | Response |
| --- | --- | --- | --- |
| POST | `/auth/register/` | `username, email, password, password2, display_name` | `201 { user, access, refresh }` |
| POST | `/auth/login/` | `email, password` | `{ user, access, refresh }` |
| POST | `/auth/logout/` | `refresh` | `205` |
| POST | `/auth/token/refresh/` | `refresh` | `{ access }` |
| POST | `/auth/password/forgot/` | `email` | `200 { detail, reset_url? }` (`reset_url` only in DEBUG) |
| POST | `/auth/password/reset/` | `uid, token, new_password, new_password2` | `{ detail }` |
| GET | `/auth/me/` | – | `{ user, profile }` |
| PATCH | `/auth/me/` | `display_name, email` | updated `user` |

`user` shape everywhere: `{ id, username, email, display_name, role, is_staff, date_joined }`.

## users & profiles
| GET/PATCH | `/users/me/profile/` | profile fields | `Profile` |
| GET | `/users/{id}/` | – | public profile (only fields the owner marked public) |
| GET | `/users/{id}/badges/` | – | earned achievements |
| POST | `/users/{id}/follow/` | – | `{ following, followers_count }` (toggle) |

`Profile`: `id, user, avatar, bio, headline, interests[], skill_level, learning_technologies[],
is_profile_public, show_email, show_projects, show_badges, total_xp, level, current_streak,
longest_streak, weekly_goal_minutes, followers_count, following_count, joined_at`.

## learning
| GET | `/learning/paths/` | – | `[{ id, slug, title, description, level, color, course_count, completed_course_count }]` |
| GET | `/learning/courses/` | `?search&level&path&category&ordering&page` | course cards |
| POST | `/learning/courses/` (admin) | course fields | `201` |
| GET/PATCH/DELETE | `/learning/courses/{id}/` | – | `?slug` lookup also accepted |
| POST | `/learning/courses/{id}/enroll/` | – | `{ enrolled: true }` |
| DELETE | `/learning/courses/{id}/enroll/` | – | `{ enrolled: false }` |
| GET | `/learning/courses/{id}/curriculum/` | – | modules + lessons, each lesson carries `completed`, `bookmarked`, `locked` |
| GET | `/learning/lessons/{id}/` | – | lesson detail incl. `quiz` |
| POST | `/learning/lessons/{id}/complete/` | – | `{ completed, xp_awarded, duplicate }` (idempotent) |
| POST | `/learning/lessons/{id}/bookmark/` | – | `{ bookmarked }` (toggle) |
| POST | `/learning/quizzes/{id}/submit/` | `answers: [{ question_id, choice_index }]` | `{ score_percent, passed, correct, total, results[] }` |
| GET | `/learning/me/enrollments/` | – | enrollments with progress % |
| GET | `/learning/me/certificates/` | – | issued certificates |
| GET | `/learning/me/certificates/{id}/` | – | certificate payload for print/PDF |

`Course`: `id, slug, title, subtitle, description, level, duration_hours, category, thumbnail,
objectives[], path, instructor { id, display_name, headline }, lesson_count, total_lessons,
enrolled_count, progress_percent, completed_lesson_count, is_enrolled, is_completed`.
`Lesson`: `id, course, module, title, kind (text|code|quiz), body_blocks[], code_example { language,
code }, position, estimated_minutes, xp`. Body blocks are `{ type: heading|paragraph|list|code|note|image, ... }`.

## dashboard
`GET /dashboard/` →
```
{ greeting, xp, level, level_progress_percent, next_level_xp,
  enrolled_courses, completed_lessons, completion_rate_percent,
  continue_learning: [ { course, lesson, progress_percent, next_position } ],
  streak: { current, longest, last_activity_date, activity_dates: ["YYYY-MM-DD"] },
  weekly_activity: [ { date, minutes, lessons_completed } ],
  weekly_goal: { target_minutes, actual_minutes, achieved },
  upcoming_events: [ { id, kind, title, starts_at } ],
  recommended_courses: [ course ], community_activity: [ post ],
  achievements: [ { badge, title, description, earned_at } ],
  quick_links: { projects, mentors, challenges } }
```

## challenges
| GET | `/challenges/` | `?difficulty&category&search&ordering&page` | challenge cards (no starter leaks of tests) |
| GET | `/challenges/{id}/` | – | detail incl. `examples`, `starter_code{javascript,python}`, `function_name` |
| POST | `/challenges/{id}/run/` | `{ language, code }` | `{ ok, results: [{ name, passed, expected, actual, error }], runtime_ms }` — **not** scored, no XP |
| POST | `/challenges/{id}/submit/` | `{ language, code }` | submission object + `points_awarded`, `first_solve_bonus` |
| GET | `/challenges/submissions/me/` | `?challenge&page` | submission history |
| GET | `/challenges/{id}/submissions/me/` | – | best + recent |
| GET | `/challenges/leaderboard/` | `?period=weekly|alltime` | `[{ rank, user, display_name, avatar, points, solved_count }]` |

`Submission`: `id, challenge, language, code, passed_count, total_tests, passed, score, points_awarded,
runtime_ms, error, created_at`.

Execution never happens in Django: `run/` and `submit/` proxy to the isolated runner service
(`runner/`, port 8090) over HTTP with a shared secret, and the runner enforces CPU/memory/timeout caps,
an AST/network allowlist for Python, and an empty-realm child process per JavaScript submission.
Both endpoints share the `sandbox` rate-limit scope (20/minute per account, `THROTTLE_SANDBOX`), since
each call starts a real process; exceeding it is `429` with a `detail` message. Browsing the
catalogue is not limited by that scope.

## community
| GET | `/community/posts/` | `?type=question\|discussion\|showcase&tag&search&ordering&page` | feed |
| POST | `/community/posts/` | `title, body, type, tags[], course?` | `201` |
| GET/PATCH/DELETE | `/community/posts/{id}/` | – | DELETE: author or admin |
| POST | `/community/posts/{id}/comments/` | `body, parent?` | comment |
| DELETE | `/community/comments/{id}/` | – | author or admin |
| POST | `/community/posts/{id}/like/` | – | `{ liked, likes_count }` (toggle) |
| POST | `/community/posts/{id}/bookmark/` | – | `{ bookmarked }` (toggle) |
| POST | `/community/posts/{id}/helpful/` | – | answer marker for questions (author or admin) |
| POST | `/community/{posts\|projects}/{id}/report/` | `reason, details` | `201` Report |
| GET | `/community/projects/` | `?technology&search&ordering=trending\|recent\|most_liked&page` | gallery |
| POST | `/community/projects/` | `title, description, technologies[], repo_url, live_url, screenshot` | `201` |
| GET/PATCH/DELETE | `/community/projects/{id}/` | – | author or admin |
| POST | `/community/projects/{id}/{like\|bookmark}/` | – | toggle counts |
| GET | `/community/me/bookmarks/` | – | `{ posts, projects }` |

Trending = likes + 2×comments + bookmarks decayed by post age (computed in the DB, not hardcoded).

## mentorship
| GET | `/mentorship/mentors/` | `?expertise&search` | approved mentors |
| GET | `/mentorship/mentors/{id}/` | – | mentor detail + availability |
| GET/PATCH | `/mentorship/mentors/me/` | `expertise[], bio, availability_note, hourly_openness, is_approved` | mentor record (role `mentor` only) |
| GET | `/mentorship/requests/` | `?status` | learner's outgoing requests |
| POST | `/mentorship/requests/` | `mentor, goal, message, preferred_slots[]` | `201` (dedup one open request per mentor) |
| GET | `/mentorship/requests/incoming/` | – | mentor's inbox (403 for learners) |
| POST | `/mentorship/requests/{id}/accept/` | `note` | mentor only |
| POST | `/mentorship/requests/{id}/decline/` | `reason` | mentor only |
| POST | `/mentorship/requests/{id}/cancel/` | – | learner only, while pending |
| GET/POST | `/mentorship/sessions/` | `request, starts_at, duration_minutes, meeting_url, agenda` | sessions; URL mentor-only |
| PATCH/DELETE | `/mentorship/sessions/{id}/` | – | mentor only (learner may cancel attendance) |
| POST | `/mentorship/sessions/{id}/attendance/` | `{ attended }` | after the session |

Statuses: `pending`, `accepted`, `declined`, `cancelled`, `completed`.

## gamification
| GET | `/achievements/` | – | catalogue with `is_earned` |
| GET | `/achievements/me/` | – | earned badges + XP totals |
| GET | `/achievements/leaderboard/` | `?period=weekly|alltime&scope=xp\|streak` | rankings |
| GET/PATCH | `/achievements/me/goals/` | `weekly_goal_minutes` | goal progress |
| GET | `/achievements/me/levels/` | – | level table + current position |

XP is awarded only by verified server actions (lesson completion, passing a quiz, a passing challenge
submission, course completion, first project publish) and is recorded in `PointEvent`, which has a
unique constraint on `(user, source_type, source_id, reason)` so repeat submissions cannot double-award.

## notifications
| GET | `/notifications/` | `?unread_only&page` | list |
| GET | `/notifications/unread-count/` | – | `{ count }` |
| POST | `/notifications/{id}/read/` | – | mark one |
| POST | `/notifications/read-all/` | – | bulk |
| DELETE | `/notifications/{id}/` | – | dismiss |

Kinds: `comment, reply, mentorship_update, session_reminder, course_announcement, challenge_result, achievement`.

## admin
| GET | `/admin/overview/` | platform counters (users, courses, enrollments, posts, reports, submissions) |
| GET | `/admin/analytics/` | `?metric=signups\|enrollments\|submissions\|activity&days=7\|30\|90` → `{ labels[], series[] }` |
| GET/PATCH | `/admin/users/`, `/admin/users/{id}/` | `?search&role&is_active`; PATCH `role, is_active` |
| CRUD | `/admin/courses/`, `/admin/lessons/`, `/admin/paths/`, `/admin/challenges/` | management tables |
| GET | `/admin/reports/` | `?status` |
| POST | `/admin/reports/{id}/resolve/` | `action=dismiss\|remove_content, note` |
| GET/POST/DELETE | `/admin/announcements/` | broadcast to enrolled users of a course |

## site (public, unauthenticated)
| GET | `/site/stats/` | – | `{ learners, courses, lessons, projects, mentor_matches, challenge_solves, countries }` — counts of real rows only; the landing page renders these and never invents numbers |
| GET | `/site/testimonials/` | – | published testimonials curated by admins; `[]` until an admin publishes one, at which point the UI labels its placeholder clearly |
| GET | `/site/events/` | – | upcoming community events `{ id, title, kind, starts_at, url }` |

## media
Uploads go to `/api/uploads/` (`multipart/form-data`, field `file`) and return `{ url }`; avatars and
project screenshots use it. Served from `MEDIA_ROOT` in development only.

The format is read from the file's own bytes, never from the declared `Content-Type`: PNG, JPEG, WebP
and GIF are stored under the extension of what they actually are, anything else is `415` (an HTML or
SVG document posted as `image/png` would otherwise be served back from the API's own origin).
Over 4 MB is `413`. Authenticated, and rate-limited per account (the `uploads` scope, 30/hour by
default) because each accepted file costs disk, not CPU. A refusal is `{ file: "…" }`, not `detail`.
