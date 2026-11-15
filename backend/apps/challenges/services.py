"""Challenge evaluation.

`run()` is a throwaway execution against the visible test cases. `submit()`
executes every case including the hidden ones, stores the submission, and awards
points only the first time a challenge is solved.
"""

import logging

from django.db import transaction
from django.db.models import F

from apps.achievements.services import award_xp, evaluate_achievements, recalculate_streak, touch_activity
from apps.challenges.models import Challenge, Submission
from apps.challenges.runner_client import RunnerPayloadTooLarge, run as runner_run

logger = logging.getLogger("apps.challenges")


class LanguageNotAllowed(Exception):
    pass


def _tests_for(challenge, include_hidden):
    tests = challenge.test_cases.all()
    if not include_hidden:
        tests = tests.filter(is_public=True)
    return [
        {"name": test.name, "args": test.args or [], "expected": test.expected}
        for test in tests
    ]


def _normalise(language):
    return (language or "javascript").strip().lower()


def run(user, challenge, code, language):
    """Trial run against public tests only — hidden tests stay invisible."""
    language = _normalise(language)
    if language not in (challenge.allowed_languages or ["javascript"]):
        raise LanguageNotAllowed(f"{language} is not allowed for this challenge.")

    tests = _tests_for(challenge, include_hidden=False)
    if not tests:
        return {"ok": False, "error": "This challenge has no public test cases yet.", "results": []}

    report = runner_run(
        code=code,
        language=language,
        function_name=challenge.function_name,
        tests=tests,
        time_limit_ms=challenge.time_limit_ms,
        memory_limit_mb=challenge.memory_limit_mb,
    )
    passed = sum(1 for result in report["results"] if result.get("passed"))
    report["summary"] = {"passed": passed, "total": len(tests)}
    return report


def submit(user, challenge, code, language):
    """Graded submission persisted with a full runner report."""
    language = _normalise(language)
    if language not in (challenge.allowed_languages or ["javascript"]):
        raise LanguageNotAllowed(f"{language} is not allowed for this challenge.")

    tests = _tests_for(challenge, include_hidden=True)
    if not tests:
        raise ValueError("This challenge has no test cases configured.")

    try:
        report = runner_run(
            code=code,
            language=language,
            function_name=challenge.function_name,
            tests=tests,
            time_limit_ms=challenge.time_limit_ms,
            memory_limit_mb=challenge.memory_limit_mb,
        )
    except RunnerPayloadTooLarge as exc:
        submission = Submission.objects.create(
            user=user,
            challenge=challenge,
            language=language,
            code=code[:20000],
            total_tests=len(tests),
            error=str(exc),
        )
        Challenge.objects.filter(pk=challenge.pk).update(submission_count=F("submission_count") + 1)
        return submission, report_error(str(exc))

    results = report.get("results", [])
    passed_count = sum(1 for result in results if result.get("passed"))
    total = len(results) or len(tests)
    passed_all = total > 0 and passed_count == total and not report.get("error")
    score = round(100 * passed_count / total) if total else 0

    already_solved = Submission.objects.filter(user=user, challenge=challenge, passed=True).exists()

    with transaction.atomic():
        submission = Submission.objects.create(
            user=user,
            challenge=challenge,
            language=language,
            code=code[:20000],
            passed_count=passed_count,
            total_tests=total,
            passed=passed_all,
            score=score,
            runtime_ms=int(report.get("runtime_ms") or 0),
            error=report.get("error") or "",
            runner_report=results,
            is_first_solve=False,
        )
        Challenge.objects.filter(pk=challenge.pk).update(submission_count=F("submission_count") + 1)

        if passed_all and not already_solved:
            submission.is_first_solve = True
            submission.save(update_fields=["is_first_solve", "updated_at"])
            Challenge.objects.filter(pk=challenge.pk).update(accepted_count=F("accepted_count") + 1)
            points = int(round(challenge.points * challenge.difficulty_weight))
            awarded, _ = award_xp(
                user,
                points,
                reason="challenge_solve",
                source_type="challenge",
                source_id=challenge.pk,
                note=challenge.title,
            )
            submission.points_awarded = points if awarded else 0
            submission.save(update_fields=["points_awarded", "updated_at"])
            touch_activity(user, challenges=1, xp=submission.points_awarded)
            recalculate_streak(user)
            _notify_solve(user, challenge, submission)

    if passed_all:
        evaluate_achievements(user)

    return submission, report


def _notify_solve(user, challenge, submission):
    from apps.notifications.services import notify

    notify(
        user,
        kind="challenge_result",
        title=f"Challenge solved: {challenge.title}",
        body=f"+{submission.points_awarded} XP for the first accepted solution.",
        link=f"/challenges/{challenge.slug}",
        dedupe_key=f"challenge-solve:{challenge.pk}:{user.pk}",
    )


def report_error(message):
    return {"ok": False, "error": message, "results": [], "runtime_ms": 0}


def personal_best(user, challenge):
    return (
        Submission.objects.filter(user=user, challenge=challenge)
        .order_by("-passed", "-score", "-created_at")
        .first()
    )
