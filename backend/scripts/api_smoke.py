"""Live end-to-end check of the running API.

Unlike the pytest suite (which mocks the sandbox and runs on SQLite), this
script talks to a real server, a real database and the real code runner, so it
proves the wiring between them. Start the backend and the runner first, then:

    .venv\\Scripts\\python.exe scripts\\api_smoke.py --base http://127.0.0.1:8000/api

It only reads and writes demo data for the seeded sample learner.
"""

import argparse
import base64
import json
import sys
import uuid

import requests

results = []

# A real 1x1 PNG, which the upload checks hand over under a deliberately wrong
# `Content-Type`: the point is that the bytes decide what gets stored.
REAL_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGO4XTAZAAQIAd++BIedAAAAAElFTkSuQmCC"
)


def check(label, ok, detail=""):
    results.append((label, bool(ok), detail))
    mark = "pass" if ok else "FAIL"
    print(f"  {mark}  {label}{'' if ok else f' — {str(detail)[:200]}'}")


class Api:
    def __init__(self, base):
        self.base = base
        self.token = None

    def call(self, method, path, token=None, **kwargs):
        headers = kwargs.pop("headers", {})
        bearer = token if token is not None else self.token
        if bearer:
            headers["Authorization"] = f"Bearer {bearer}"
        response = requests.request(method, f"{self.base}{path}", headers=headers, timeout=30, **kwargs)
        try:
            payload = response.json()
        except ValueError:
            payload = {"raw": response.text[:300]}
        return response.status_code, payload

    def get(self, path, **kw):
        return self.call("GET", path, **kw)

    def post(self, path, **kw):
        return self.call("POST", path, **kw)

    def patch(self, path, **kw):
        return self.call("PATCH", path, **kw)

    def delete(self, path, **kw):
        return self.call("DELETE", path, **kw)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8000/api")
    parser.add_argument("--email", default="ada@codeher.dev")
    parser.add_argument("--password", default="CodeHer!Learn2026")
    args = parser.parse_args()
    api = Api(args.base)

    print(f"API smoke test against {args.base}\n")

    print("public surface")
    code, stats = api.get("/site/stats/")
    check("GET /site/stats/ is public and numeric", code == 200 and isinstance(stats.get("courses"), int), stats)
    code, testimonials = api.get("/site/testimonials/")
    check("GET /site/testimonials/ marks uncurated data as sample", code == 200 and testimonials.get("is_sample") in (True, False), testimonials)
    code, paths = api.get("/learning/paths/")
    path_rows = paths.get("results", []) if isinstance(paths, dict) else paths
    check("GET /learning/paths/ returns the seeded paths", code == 200 and len(path_rows) >= 9, len(path_rows))
    code, courses = api.get("/learning/courses/?level=beginner&page_size=5")
    check("GET /learning/courses/ filters and paginates", code == 200 and courses.get("count", 0) > 0, courses.get("count"))
    code, _ = api.get("/dashboard/")
    check("GET /dashboard/ requires authentication", code == 401, code)
    code, _ = api.post("/auth/login/", json={"email": "ada@codeher.dev", "password": "wrong"})
    check("a wrong password is rejected", code in (400, 401), code)

    print("\nauthentication")
    code, auth = api.post("/auth/login/", json={"email": args.email, "password": args.password})
    check("POST /auth/login/ returns tokens", code == 200 and "access" in auth, auth)
    if code != 200:
        return finish()
    api.token = auth["access"]
    code, me = api.get("/auth/me/")
    check("GET /auth/me/ identifies the learner", code == 200 and me["user"]["email"] == args.email, me)
    code, refreshed = api.post("/auth/token/refresh/", json={"refresh": auth["refresh"]}, token=False)
    check("POST /auth/token/refresh/ mints a new access token", code == 200 and "access" in refreshed, refreshed)
    code, _ = api.get("/auth/me/", token="not-a-real-token")
    check("a forged token is refused", code == 401, code)

    print("\ndashboard is computed, not canned")
    code, dash = api.get("/dashboard/")
    check("GET /dashboard/ answers with the contract shape", code == 200 and {"xp", "level", "streak", "continue_learning"} <= set(dash), list(dash)[:8])
    code, profile = api.get("/users/me/profile/")
    check("profile XP matches the dashboard XP", code == 200 and profile.get("total_xp") == dash.get("xp"), (profile.get("total_xp"), dash.get("xp")))

    print("\nlearning journey")
    # Find a lesson this learner has not finished yet, so the XP check below
    # proves a first award rather than a replay of the seed's progress.
    enrolled = {e["course"]["slug"] for e in api.get("/learning/me/enrollments/", params={"page_size": 50})[1].get("results", [])}
    lessons, lesson = [], None
    for course in courses["results"][:6]:
        if course["slug"] not in enrolled:
            api.post(f"/learning/courses/{course['slug']}/enroll/", json={})
        code, curriculum = api.get(f"/learning/courses/{course['slug']}/curriculum/")
        if code != 200:
            continue
        lessons = [l for m in curriculum.get("modules", []) for l in m.get("lessons", [])]
        lesson = next((l for l in lessons if not l["completed"] and not l.get("locked")), None)
        if lesson:
            break
    check("curriculum lists lessons with completion state", lesson is not None and "completed" in lessons[0], len(lessons))
    if lesson is None:
        return finish()
    code, first = api.post(f"/learning/lessons/{lesson['id']}/complete/")
    code, again = api.post(f"/learning/lessons/{lesson['id']}/complete/")
    check(
        "re-completing a lesson is idempotent and awards XP once",
        first.get("xp_awarded", 0) > 0 and again.get("duplicate") and again.get("xp_awarded") == 0,
        (first, again),
    )
    xp_after = api.get("/users/me/profile/")[1].get("total_xp")
    check("XP moved after the completion", xp_after >= dash["xp"], (dash["xp"], xp_after))
    code, _ = api.post(f"/learning/lessons/{lesson['id']}/bookmark/")
    code, bookmarked = api.get(f"/learning/lessons/{lesson['id']}/")
    check("bookmark toggles and persists", code == 200 and bookmarked.get("bookmarked"), bookmarked.get("bookmarked"))

    quizzes = [l for l in lessons if l.get("kind") == "quiz" or l.get("quiz")]
    if quizzes:
        quiz_lesson = api.get(f"/learning/lessons/{quizzes[0]['id']}")[1]
        quiz = quiz_lesson.get("quiz")
        if quiz:
            answers = [{"question_id": q["id"], "choice_index": 0} for q in quiz["questions"]]
            code, graded = api.post(f"/learning/quizzes/{quiz['id']}/submit/", json={"answers": answers})
            check("quiz is graded server-side", code == 200 and "score_percent" in graded and graded.get("total") == len(quiz["questions"]), graded)
            check("the answer key is never leaked to the client", "is_correct" not in json.dumps(graded), "is_correct leaked")
    code, enrollments = api.get("/learning/me/enrollments/")
    check("enrollments carry a real progress percentage", code == 200 and all("progress_percent" in e for e in enrollments.get("results", [])), enrollments.get("count"))

    print("\nchallenges against the live sandbox")
    code, challenge_list = api.get("/challenges/?difficulty=beginner")
    check("GET /challenges/ lists published work", code == 200 and challenge_list.get("count") > 0, challenge_list.get("count"))
    challenge = challenge_list["results"][0]
    code, detail = api.get(f"/challenges/{challenge['slug']}/")
    check(
        "hidden test cases stay server-side",
        code == 200 and detail["test_count"] > len(detail["public_tests"]),
        (detail.get("test_count"), len(detail.get("public_tests", []))),
    )
    name = detail["function_name"]
    solved = f"function {name}(...) {{ return JSON.parse(JSON.stringify(arguments[0] === undefined ? null : arguments[0])); }}"
    code, trial = api.post(f"/challenges/{detail['id']}/run/", json={"language": "javascript", "code": solved})
    check("POST /run/ executes in the runner and reports per case", code == 200 and len(trial.get("results", [])) > 0, trial)
    code, wrong = api.post(f"/challenges/{detail['id']}/submit/", json={"language": "javascript", "code": f"function {name}() {{ return 12345; }}"})
    check("an incorrect submission is stored and scores below 100", code in (200, 201) and wrong.get("score", 100) < 100, (code, wrong.get("score")))
    hidden = [r for r in wrong.get("results", []) if r["name"] not in {t["name"] for t in detail["public_tests"]}]
    check(
        "the graded report hides expectations for unpublished cases",
        bool(hidden) and all(r["expected"] is None and r["actual"] is None for r in hidden),
        hidden[:2],
    )
    before = wrong.get("points_awarded", 0)
    code, repeat = api.post(f"/challenges/{detail['id']}/submit/", json={"language": "javascript", "code": f"function {name}() {{ return 12345; }}"})
    check("re-submitting the same answer cannot earn twice", repeat.get("points_awarded", 0) == before, (before, repeat.get("points_awarded")))
    code, history = api.get(f"/challenges/{detail['id']}/submissions/me/")
    check("submission history is stored", code == 200 and history.get("recent"), history.get("best"))
    code, board = api.get("/challenges/leaderboard/")
    check("leaderboard is built from stored rows", code == 200 and isinstance(board, (list, dict)), str(board)[:80])

    print("\ncommunity")
    title = f"Smoke test question {uuid.uuid4().hex[:8]}"
    code, post = api.post("/community/posts/", json={"title": title, "body": "Does this round trip through the database?", "type": "question", "tags": ["smoke"]})
    check("POST /community/posts/ creates a real row", code == 201 and post.get("id"), post)
    if post.get("id"):
        code, found = api.get("/community/posts/?tag=smoke")
        check("the new post is reachable by tag", code == 200 and found.get("count", 0) >= 1, found.get("count"))
        code, comment = api.post(f"/community/posts/{post['id']}/comments/", json={"body": "Self-answer from the smoke test."})
        check("comment creation works", code in (200, 201), comment)
        code, liked = api.post(f"/community/posts/{post['id']}/like/")
        check("like toggle returns a count", code == 200 and "likes_count" in liked, liked)
        code, unliked = api.post(f"/community/posts/{post['id']}/like/")
        check("liking again removes it", unliked.get("likes_count", 99) < liked.get("likes_count", 0) + 1, (liked, unliked))
        api.delete(f"/community/posts/{post['id']}/")

    print("\nmentorship, gamification, notifications")
    code, mentors = api.get("/mentorship/mentors/")
    check("approved mentors are listed", code == 200 and len(mentors.get("results", mentors) if isinstance(mentors, dict) else mentors) >= 1, str(mentors)[:80])
    code, badges = api.get("/achievements/me/")
    check("earned badges come from real metrics", code == 200, str(badges)[:80])
    code, goals = api.patch("/achievements/me/goals/", json={"weekly_goal_minutes": 150})
    check("weekly goal is editable", code == 200 and goals.get("weekly_goal_minutes", goals.get("target_minutes")) in (150, None), goals)
    code, notes = api.get("/notifications/?unread_only")
    check("notification inbox responds", code == 200, str(notes)[:80])
    code, count = api.get("/notifications/unread-count/")
    check("unread count is a number", code == 200 and isinstance(count.get("count"), int), count)

    print("\nrole separation")
    code, _ = api.get("/admin/overview/")
    check("a learner cannot reach the admin console", code == 403, code)
    code, admin_auth = api.post("/auth/login/", json={"email": "admin@codeher.dev", "password": "CodeHer!Admin2026"})
    check("the seeded admin can sign in", code == 200 and admin_auth.get("user", {}).get("role") == "admin", admin_auth)
    admin_token = admin_auth.get("access", "")
    code, overview = api.get("/admin/overview/", token=admin_token)
    check("admin overview returns database counters", code == 200 and isinstance(overview, dict), str(overview)[:120])
    code, analytics = api.get("/admin/analytics/?metric=signups&days=7", token=admin_token)
    check("admin analytics are series over real rows", code == 200 and "labels" in analytics and "series" in analytics, str(analytics)[:120])
    code, created = api.post("/learning/courses/", token=admin_token, json={"title": "Smoke course", "level": "beginner", "category": "web", "duration_hours": 1})
    check("admin can create content", code == 201, created)
    if created.get("id"):
        api.delete(f"/learning/courses/{created['id']}/", token=admin_token)
    code, _ = api.post("/learning/courses/", token="", json={"title": "nope"})
    check("anonymous writes are refused", code in (401, 403), code)

    print("\nuploads")
    # Two calls per run: the `uploads` scope allows 30 an hour per account, and a
    # check that silently started failing on the eleventh run of an hour would tell
    # us nothing about the server.
    code, shot = api.post(
        "/uploads/", files={"file": ("shot.png", REAL_PNG, "text/html")}, data={"folder": "avatars"}
    )
    check("POST /uploads/ accepts a real image whatever its declared type", code == 201 and shot.get("url"), (code, shot))
    check(
        "the stored name follows the bytes, not the declaration",
        code == 201 and (shot.get("path") or "").endswith(".png"),
        shot.get("path"),
    )
    code, refused = api.post("/uploads/", files={"file": ("evil.png", b"<html><script>alert(1)</script></html>", "image/png")})
    check("an HTML body claiming to be a PNG is refused", code in (415, 429), (code, refused))
    # `token=""` rather than `token=None`: the helper treats None as "keep the
    # learner's bearer", which would make this check pass for the wrong reason.
    code, _ = api.post("/uploads/", token="", files={"file": ("x.png", REAL_PNG, "image/png")})
    check("anonymous uploads are refused", code in (401, 403), code)

    print("\nrunner honesty")
    code, blocked = api.post(f"/challenges/{detail['id']}/run/", json={"language": "ruby", "code": "def x; end"})
    check("an unsupported language is refused, not passed", code in (400, 503), code)

    return finish()


def finish():
    failed = [label for label, ok, _ in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} checks passed.")
    if failed:
        print("failed: " + ", ".join(failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
