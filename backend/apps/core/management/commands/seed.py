"""Seed CodeHer with real, database-backed demonstration content.

Everything this command writes is an actual row: courses are queried through the
same serializers the API uses, community counters are recomputed by the same
services, and the sample learner progress goes through the real completion,
quiz-grading and achievement code paths. No frontend screen is fed a hardcoded
array to look alive.

Run it after `manage.py migrate`:

    python manage.py seed
    python manage.py seed --no-progress   # content only, no simulated activity

It refuses to run against a database that is not on this machine, because the demo
accounts it creates have passwords published in this repository; `--force` overrides
that once you have confirmed the database is disposable.
"""

from datetime import timedelta

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connections, transaction
from django.utils import timezone

from apps.achievements import services as badge_services
from apps.achievements.models import Achievement
from apps.challenges.models import Challenge, ChallengeTestCase
from apps.community import services as community_services
from apps.community.models import Engagement, Post, Project
from apps.courses.models import Course, CourseModule, LearningPath, Lesson, Quiz, QuizQuestion
from apps.mentorship import services as mentorship_services
from apps.mentorship.models import MentorProfile
from apps.core.models import Event
from apps.progress import services as progress_services
from apps.users.models import Profile, User

from apps.core.seed import curriculum_backend, curriculum_career, curriculum_react, curriculum_web
from apps.core.seed.badges import ACHIEVEMENTS
from apps.core.seed.challenges_seed import CHALLENGES
from apps.core.seed.community_seed import DEMO_PASSWORD, EVENTS, MENTORS, PEOPLE, POSTS, PROJECTS


PATH_ORDER = [
    "html-css-fundamentals",
    "javascript-for-beginners",
    "react",
    "python-programming",
    "django-backend-development",
    "mysql-and-database-design",
    "git-and-github",
    "full-stack-web-development",
    "introduction-to-cybersecurity",
]


def curriculum_paths():
    """Every uppercase dict in the curriculum modules, in catalog order."""
    found = {}
    for module in (curriculum_web, curriculum_react, curriculum_backend, curriculum_career):
        for name, value in vars(module).items():
            if name.isupper() and isinstance(value, dict) and "courses" in value:
                found[value["slug"]] = value
    ordered = [found.pop(slug) for slug in PATH_ORDER if slug in found]
    return ordered + sorted(found.values(), key=lambda path: path["title"])


def local_database(database):
    """True when a connection cannot possibly be a shared or production cluster.

    SQLite is a file on this machine, and an empty or loopback host is a server on this
    machine. Everything else is somebody else's database, however casually it is named.
    """
    host = (database.get("HOST") or "").strip().lower()
    return database["ENGINE"].endswith("sqlite3") or host in {"", "127.0.0.1", "localhost", "::1"}


class Command(BaseCommand):
    help = "Create sample courses, challenges, badges, accounts and community content."

    def add_arguments(self, parser):
        parser.add_argument("--no-progress", action="store_true", help="Skip the simulated learner activity.")
        parser.add_argument(
            "--force", action="store_true", help="Seed a database that is not on this machine anyway."
        )

    def refuse_remote_database(self, force):
        """Stop the demo accounts from being written into a real cluster.

        Their passwords live in this repository, in plain sight, and the README tells
        people to run this command — so an environment whose .env points at TiDB Cloud
        would otherwise gain a working admin login that anyone reading GitHub has.
        """
        database = connections["default"].settings_dict
        if force or local_database(database):
            return
        raise CommandError(
            f"Refusing to seed {database.get('NAME')} on {database.get('HOST')}: the demo "
            "accounts in apps/core/seed/community_seed.py have published passwords. Pass "
            "--force if this is a disposable database you control."
        )

    def handle(self, *args, **options):
        self.refuse_remote_database(options["force"])

        # A missing migration must never be papered over by a partial seed.
        call_command("migrate", verbosity=0, interactive=False)

        with transaction.atomic():
            people = self.seed_people()
            paths = self.seed_curriculum(people)
            badges = self.seed_badges()
            challenges = self.seed_challenges()
            community = self.seed_community(people, paths)
            network = self.seed_network(people)
            mentorship = self.seed_mentorship(people)
            events = self.seed_events()
            progress = {} if options["no_progress"] else self.seed_progress(people, paths)

        self.stdout.write(self.style.SUCCESS("Seed complete."))
        rows = [
            ("members", len(people)),
            ("learning paths", len(paths)),
            ("courses", Course.objects.count()),
            ("lessons", Lesson.objects.count()),
            ("quizzes", Quiz.objects.count()),
            ("badges", badges),
            ("challenges", challenges),
            ("posts", community["posts"]),
            ("projects", community["projects"]),
            ("follows", network),
            ("mentor matches", mentorship),
            ("events", events),
        ]
        for label, count in rows:
            self.stdout.write(f"  {label:<16} {count}")
        for label, count in progress.items():
            self.stdout.write(f"  {label:<16} {count}")
        self.stdout.write("")
        self.stdout.write("  Sign in with ada@codeher.dev / CodeHer!Learn2026,")
        self.stdout.write("                grace@codeher.dev / CodeHer!Mentor2026, or")
        self.stdout.write("                admin@codeher.dev / CodeHer!Admin2026.")
        self.stdout.write(f"  Sample members (nia, sofia, omid, mei @codeher.dev) all use {DEMO_PASSWORD}.")

    # ------------------------------------------------------------- members
    def seed_people(self):
        people = {}
        for key, spec in PEOPLE.items():
            user, _ = User.objects.update_or_create(
                email=spec["email"],
                defaults={
                    "username": spec["username"],
                    "display_name": spec["display_name"],
                    "role": spec["role"],
                    "is_active": True,
                    "is_staff": spec["role"] == "admin",
                },
            )
            user.set_password(spec.get("password") or DEMO_PASSWORD)
            user.save(update_fields=["password"])

            profile, _ = Profile.objects.get_or_create(user=user)
            for field in ("headline", "bio", "interests", "learning_technologies", "skill_level", "country",
                          "timezone_name", "weekly_goal_minutes"):
                setattr(profile, field, spec.get(field, getattr(profile, field)))
            profile.save()

            people[key] = user
            self.stdout.write(f"  member {user.email} ({user.role})")

        for key, spec in MENTORS.items():
            mentor, _ = MentorProfile.objects.update_or_create(
                user=people[key],
                defaults={**spec, "is_approved": True, "is_accepting": True, "approved_by": people["admin"]},
            )
            self.stdout.write(f"  mentor {mentor.user.email} (sample profile)")
        return people

    # ---------------------------------------------------------- curriculum
    def seed_curriculum(self, people):
        instructors = [people["grace"], people["mei"]]
        paths = curriculum_paths()

        for path_position, path_spec in enumerate(paths, start=1):
            path, _ = LearningPath.objects.update_or_create(
                slug=path_spec["slug"],
                defaults={
                    "title": path_spec["title"],
                    "description": path_spec.get("description", ""),
                    "level": path_spec["level"],
                    "color": path_spec["color"],
                    "icon": path_spec.get("icon", ""),
                    "position": path_position,
                    "is_published": True,
                },
            )

            for course_position, course_spec in enumerate(path_spec["courses"], start=1):
                course = self._seed_course(path, course_spec, course_position, instructors)
                self._seed_modules(course, course_spec["modules"])

        return paths

    def _seed_course(self, path, spec, position, instructors):
        lesson_total = sum(len(module["lessons"]) for module in spec["modules"])
        minutes = sum(
            lesson.get("estimated_minutes", 10) for module in spec["modules"] for lesson in module["lessons"]
        )
        objectives = spec.get("objectives", [])
        description = (
            f"{spec.get('subtitle', '')}\n\n"
            f"You will work through {len(spec['modules'])} modules and {lesson_total} lessons "
            f"(about {max(1, round(minutes / 60))} hours of practice), covering "
            f"{', '.join(objective.lower() for objective in objectives)}."
        )
        course, _ = Course.objects.update_or_create(
            slug=slugify_course(spec["title"]),
            defaults={
                "title": spec["title"],
                "subtitle": spec.get("subtitle", ""),
                "description": description,
                "level": spec["level"],
                "category": spec.get("category", "web"),
                "duration_hours": spec.get("duration_hours", max(1, round(minutes / 60))),
                "objectives": objectives,
                "requirements": spec.get("requirements", []),
                "learning_path": path,
                "instructor": instructors[(position - 1) % len(instructors)],
                "position": position,
                "is_published": True,
            },
        )
        progress_services.sync_counters(course)
        return course

    def _seed_modules(self, course, module_specs):
        for module_position, module_spec in enumerate(module_specs, start=1):
            module, _ = CourseModule.objects.update_or_create(
                course=course,
                position=module_position,
                defaults={
                    "title": module_spec["title"],
                    "summary": module_spec.get("summary", ""),
                },
            )
            for lesson_position, lesson_spec in enumerate(module_spec["lessons"], start=1):
                # Authored questions always become a graded quiz, whatever kind the data says.
                kind = "quiz" if lesson_spec.get("questions") else lesson_spec["kind"]
                blocks = build_body_blocks(lesson_spec)
                code_example = dict(lesson_spec.get("code") or {})
                if kind == "code" and not code_example:
                    code_example = {"language": "text", "code": "// Add a code example in the seed data."}
                lesson, _ = Lesson.objects.update_or_create(
                    module=module,
                    position=lesson_position,
                    defaults={
                        "course": course,
                        "title": lesson_spec["title"],
                        "kind": kind,
                        "summary": lesson_spec.get("summary", ""),
                        "body_blocks": blocks,
                        "code_example": code_example,
                        "estimated_minutes": lesson_spec.get("estimated_minutes", 10),
                        "is_published": True,
                    },
                )
                self._seed_quiz(lesson, lesson_spec)

    def _seed_quiz(self, lesson, spec):
        questions = spec.get("questions") or []
        if lesson.kind != "quiz":
            Quiz.objects.filter(lesson=lesson).delete()
            return
        quiz, _ = Quiz.objects.update_or_create(
            lesson=lesson,
            defaults={"title": f"{lesson.title} check", "passing_percent": 70, "max_attempts": 0},
        )
        quiz.questions.all().delete()
        for index, question in enumerate(questions, start=1):
            QuizQuestion.objects.create(
                quiz=quiz,
                prompt=question["prompt"],
                choices=[
                    {"text": text, "is_correct": index_of == question["correct"]}
                    for index_of, text in enumerate(question["choices"])
                ],
                explanation=question.get("explanation", ""),
                hint=question.get("hint", ""),
                position=index,
            )

    # ------------------------------------------------------------- badges
    def seed_badges(self):
        for spec in ACHIEVEMENTS:
            Achievement.objects.update_or_create(
                code=spec["code"],
                defaults={key: value for key, value in spec.items() if key != "code"},
            )
        return len(ACHIEVEMENTS)

    # ---------------------------------------------------------- challenges
    def seed_challenges(self):
        for position, spec in enumerate(CHALLENGES, start=1):
            challenge, _ = Challenge.objects.update_or_create(
                slug=slugify_course(spec["title"]),
                defaults={
                    "title": spec["title"],
                    "summary": spec["summary"],
                    "description": spec["description"],
                    "difficulty": spec["difficulty"],
                    "category": spec["category"],
                    "function_name": "solution",
                    "starter_code": spec["starter"],
                    "examples": spec["examples"],
                    "hints": spec["hints"],
                    "topics": spec["topics"],
                    "points": spec["points"],
                    "allowed_languages": spec["allowed_languages"],
                    "time_limit_ms": 2000,
                    "memory_limit_mb": 128,
                    "position": position,
                    "is_published": True,
                },
            )
            challenge.test_cases.all().delete()
            for index, case in enumerate(spec["tests"], start=1):
                ChallengeTestCase.objects.create(
                    challenge=challenge,
                    name=case["name"],
                    args=case["args"],
                    expected=case["expected"],
                    is_public=case.get("public", False),
                    position=index,
                )
        return len(CHALLENGES)

    # ----------------------------------------------------------- community
    def seed_community(self, people, paths):
        courses = list(Course.objects.all())

        for index, spec in enumerate(POSTS):
            course = next((c for c in courses if c.category == spec.get("course_category")), None)
            post, created = Post.objects.update_or_create(
                user=people[spec["author"]],
                title=spec["title"],
                defaults={
                    "type": spec["type"],
                    "body": spec["body"],
                    "tags": spec.get("tags", []),
                    "course": course,
                    "status": "published",
                },
            )
            if not created:
                post.comments.all().delete()
            for comment_spec in spec.get("comments", []):
                community_services.add_comment(people[comment_spec["author"]], post, comment_spec["body"])
            self._seed_engagement(post, people, index, skip=post.user_id)

        for index, spec in enumerate(PROJECTS):
            project, _ = Project.objects.update_or_create(
                user=people[spec["author"]],
                title=spec["title"],
                defaults={
                    "description": f"Sample project created by `manage.py seed`. {spec['description']}",
                    "technologies": spec["technologies"],
                    "repo_url": spec.get("repo_url", ""),
                    "live_url": spec.get("live_url", ""),
                    "views_count": spec.get("views", 0),
                    "status": "draft",
                },
            )
            # Always routed through the service: it publishes, recomputes trending,
            # and its PointEvent constraint keeps the XP award to exactly once.
            community_services.publish_project(project.user, project)
            self._seed_engagement(project, people, index, skip=project.user_id)

        community_services.refresh_all_trending()
        return {"posts": Post.objects.count(), "projects": Project.objects.count()}

    def _seed_engagement(self, target, people, index, skip):
        """Every like and bookmark below is a real Engagement row, so the feed's
        counters and the trending score are recomputed rather than asserted.

        toggle_engagement is a switch, so replaying the seed over rows that
        already exist would flip them all off and leave every counter at zero.
        Clearing the target first keeps the command idempotent.
        """
        if isinstance(target, Post):
            Engagement.objects.filter(post=target).delete()
        else:
            Engagement.objects.filter(project=target).delete()
        for position, person in enumerate(people.values()):
            if person.pk == skip:
                continue
            if position % 2 == index % 2:
                community_services.toggle_engagement(person, target, "like")
            if index % 3 == position % 3:
                community_services.toggle_engagement(person, target, "bookmark")
        community_services.refresh_counters(target)

    # ------------------------------------------------------------ network
    def seed_network(self, people):
        """A small ring of real Follow rows so profiles are not all zeroes."""
        members = [person for key, person in people.items() if key != "admin"]
        created = 0
        for index, follower in enumerate(members):
            target = members[(index + 1) % len(members)]
            if community_services.toggle_follow(follower, target):
                created += 1
        return created

    # ----------------------------------------------------------- mentorship
    def seed_mentorship(self, people):
        """One accepted match with a finished and an upcoming session, plus one
        pending request. Every status transition runs through the service, so
        the XP, counters and notifications are the ones a real match produces."""
        from apps.mentorship.models import MentorshipRequest, MentorshipSession

        pairs = [
            ("ada", "grace", "Finish the Django path and get one project deployed",
             "I have the models chapter half done but I keep stalling on migrations. I would like a "
             "review of my design before I build on top of it.", ["Tue 19:00 UTC"]),
            ("sofia", "mei", "Security review of my API before I share it",
             "It stores user records and I would like a second pair of eyes on how I handle passwords "
             "and tokens.", ["Wed 15:00 SGT"]),
        ]
        for index, (learner_key, mentor_key, goal, message, slots) in enumerate(pairs):
            learner, mentor = people[learner_key], people[mentor_key]
            existing = MentorshipRequest.objects.filter(learner=learner, mentor=mentor).first()
            if existing:
                request = existing
            else:
                request = mentorship_services.create_request(learner, mentor, goal, message, slots)
            if index != 0 or request.status != "pending":
                continue
            mentorship_services.accept_request(request, mentor, "Happy to look at your models.")
            # A finished session cannot go through schedule_session, which rightly
            # refuses past times for live users, so the history row is written directly.
            MentorshipSession.objects.get_or_create(
                request=request,
                starts_at=timezone.now() - timedelta(days=3),
                defaults={
                    "mentor": mentor,
                    "learner": learner,
                    "duration_minutes": 45,
                    "agenda": "Model review: FK direction, related names, and what to index.",
                    "meeting_url": "https://meet.example.com/codeher-sample",
                    "notes": "Rewrote two FKs and added related_name. Next step is the admin.",
                    "status": "completed",
                    "learner_attended": True,
                },
            )
            mentorship_services.schedule_session(
                request,
                mentor,
                starts_at=timezone.now() + timedelta(days=5),
                duration_minutes=45,
                agenda="Deploy checklist: settings, static files, secrets and migrations in production.",
                meeting_url="https://meet.example.com/codeher-sample",
            )

        return MentorshipRequest.objects.filter(status__in=["accepted", "completed"]).count()

    # -------------------------------------------------------------- events
    def seed_events(self):
        base = timezone.now().replace(second=0, microsecond=0, minute=0) + timedelta(hours=18)
        for spec in EVENTS:
            starts = base + timedelta(days=spec["starts_in_days"])
            Event.objects.update_or_create(
                title=spec["title"],
                defaults={
                    "description": spec["description"],
                    "kind": spec["kind"],
                    "starts_at": starts,
                    "ends_at": starts + timedelta(minutes=spec["duration_minutes"]),
                    "is_published": True,
                },
            )
        return len(EVENTS)

    # -------------------------------------------------------- demo progress
    def seed_progress(self, people, paths):
        """Run the real completion + grading services so dashboard numbers are earned."""
        ada = people["ada"]
        summary = {}

        catalog = list(Course.objects.filter(is_published=True).order_by("learning_path", "position"))
        if not catalog:
            return summary

        self._finish_course(ada, catalog[0])
        if len(catalog) > 1:
            self._partial_course(ada, catalog[1], lessons=3, quizzes=1)
        for learner, course, lessons in ((people["nia"], catalog[-1], 2), (people["sofia"], catalog[1], 1)):
            self._partial_course(learner, course, lessons=lessons)

        self._backdate_streak(ada, days=4)
        summary["sample progress"] = "generated through the completion services"
        return summary

    def _finish_course(self, user, course):
        progress_services.enroll(user, course)
        for lesson in course.lessons.filter(is_published=True):
            self._complete(user, lesson)
        self._pass_quizzes(user, course)
        badge_services.evaluate_achievements(user)

    def _partial_course(self, user, course, lessons=1, quizzes=0):
        progress_services.enroll(user, course)
        ordered = list(course.lessons.filter(is_published=True))
        for lesson in ordered[:lessons]:
            self._complete(user, lesson)
        if quizzes:
            self._pass_quizzes(user, course)

    def _complete(self, user, lesson):
        minutes = lesson.estimated_minutes or 10
        progress_services.complete_lesson(user, lesson, time_spent_seconds=minutes * 60)

    def _pass_quizzes(self, user, course):
        from apps.courses.models import Quiz as QuizModel

        for quiz in QuizModel.objects.filter(lesson__course=course):
            answers = {}
            for question in quiz.questions.all():
                correct = next(
                    (index for index, choice in enumerate(question.choices) if choice.get("is_correct")), 0
                )
                answers[question.pk] = correct
            progress_services.grade_quiz(user, quiz, answers)

    def _backdate_streak(self, user, days):
        today = timezone.localdate()
        for offset in range(1, days + 1):
            badge_services.touch_activity(user, minutes=20, day=today - timedelta(days=offset))
        badge_services.recalculate_streak(user)


def build_body_blocks(spec):
    """Turn the readable seed shape into the block list the lesson player renders."""
    blocks = []
    summary = spec.get("summary", "")
    if summary:
        blocks.append({"type": "paragraph", "text": summary})
    paragraphs = spec.get("paragraphs") or []
    if paragraphs:
        blocks.append({"type": "heading", "level": 2, "text": spec["title"]})
    for paragraph in paragraphs:
        blocks.append({"type": "paragraph", "text": paragraph})
    bullets = spec.get("bullets") or []
    if bullets:
        blocks.append({"type": "list", "ordered": False, "items": list(bullets)})
    code = spec.get("code")
    if code:
        blocks.append({"type": "heading", "level": 3, "text": code.get("caption", "Worked example")})
    if spec.get("note"):
        blocks.append({"type": "note", "variant": "tip", "title": "Remember", "text": spec["note"]})
    return blocks


def slugify_course(title):
    from django.utils.text import slugify

    return slugify(title)[:220] or "course"
