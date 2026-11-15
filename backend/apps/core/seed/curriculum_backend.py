"""Clearly labelled demonstration content for manage.py seed."""

PYTHON = {
    "title": "Python Programming",
    "slug": "python-programming",
    "level": "beginner",
    "color": "#3b82f6",
    "icon": "Terminal",
    "description": "The language behind servers, data and automation. You will read real code, predict what "
    "it prints, and write Python that is correct on purpose rather than by luck.",
    "courses": [
        {
            "title": "Python Basics: Values, Logic and Functions",
            "subtitle": "Types, control flow and functions — the parts you reach for every single day.",
            "level": "beginner",
            "category": "python",
            "duration_hours": 10,
            "objectives": [
                "Store values with the core types and format them with f-strings",
                "Branch and loop instead of copy-pasting code",
                "Write functions and build collections with comprehensions",
            ],
            "requirements": ["Any computer with Python 3.10 or newer and a text editor. No coding background assumed."],
            "modules": [
                {
                    "title": "Types and control flow",
                    "summary": "Values, printing, and the branching and looping that replace repetitive code.",
                    "lessons": [
                        {
                            "title": "Variables, types and f-strings",
                            "kind": "text",
                            "summary": "A variable is a name bound to a value; Python works out the type as you go.",
                            "paragraphs": [
                                "Python is dynamically typed: you write name = 'Ada' and the interpreter knows "
                                "'Ada' is a string without you declaring anything. That flexibility is a gift, but "
                                "it means you should keep each name's meaning stable so your code stays readable "
                                "when you return to it next month.",
                                "The everyday building blocks are str (text), int (whole numbers), float (decimal "
                                "numbers) and bool (True or False). To drop values into text, use an f-string: put "
                                "an f before the quotes and any expression inside braces. It beats string "
                                "concatenation with + on both clarity and speed.",
                            ],
                            "bullets": [
                                "Names are labels you stick on objects; rebinding is allowed but be deliberate",
                                "type(value) tells you what a value is when you are unsure",
                                "f'{price:.2f}' formats a float to two decimal places",
                                "Python has no ++ operator; use count += 1",
                            ],
                            "estimated_minutes": 12,
                        },
                        {
                            "title": "Branching and looping",
                            "kind": "code",
                            "summary": "Indentation is the syntax: a colon plus an indented block is a suite.",
                            "paragraphs": [
                                "Use if / elif / else to choose one path, and for to repeat over something you can "
                                "count. There are no braces to match, which is exactly why mixing tabs and spaces "
                                "breaks programs — configure your editor to insert four spaces.",
                                "Prefer for over while. enumerate() gives you the index and the item together, "
                                "which avoids most off-by-one errors.",
                            ],
                            "code": {
                                "language": "python",
                                "caption": "Choosing a path and repeating work",
                                "code": """def describe(streak):
    if streak <= 0:
        return "No streak yet - start with five minutes."
    elif streak < 7:
        return "Almost a week, keep going."
    else:
        return "One week strong. Set a bigger goal."

topics = ["loops", "dicts", "comprehensions"]
for index, topic in enumerate(topics, start=1):
    print(f"{index}. {topic}")""",
                            },
                            "estimated_minutes": 14,
                        },
                        {
                            "title": "Check your understanding",
                            "kind": "quiz",
                            "summary": "Four questions on values and control flow.",
                            "paragraphs": ["Four questions here — read the feedback and retake this as many times as you need."],
                            "questions": [
                                {
                                    "prompt": "Which is the clearest modern way to build text from values?",
                                    "choices": ["Joining with + signs", "An f-string like f'Hi {name}!'", "Numbering the pieces", "Concatenating in a loop"],
                                    "correct": 1,
                                    "explanation": "f-strings drop values straight into text and are the readable default.",
                                },
                                {
                                    "prompt": "How does Python know that print('hi') belongs inside the if block?",
                                    "choices": ["Curly braces", "The indentation level", "A semicolon", "The word 'end'"],
                                    "correct": 1,
                                    "explanation": "Blocks are defined purely by indentation, so inconsistent whitespace causes bugs.",
                                },
                                {
                                    "prompt": "How do you add one to a counter in Python?",
                                    "choices": ["count++", "count += 1", "++ count", "counter(count)"],
                                    "correct": 1,
                                    "explanation": "Python has no ++ operator, so you write count += 1 to add one and rebind the name.",
                                },
                                {
                                    "prompt": "Which helper gives you the index and the item together in a loop?",
                                    "choices": ["enumerate()", "range()", "zip()", "index()"],
                                    "correct": 0,
                                    "explanation": "enumerate(topics, start=1) yields each position next to its item, which avoids most off-by-one errors.",
                                },
                            ],
                            "estimated_minutes": 5,
                        },
                    ],
                },
                {
                    "title": "Functions and comprehensions",
                    "summary": "Package logic into named units and build data without hand-rolled loops.",
                    "lessons": [
                        {
                            "title": "Defining functions",
                            "kind": "text",
                            "summary": "A function takes input, does one job, and hands back a result.",
                            "paragraphs": [
                                "def name(parameters): starts a function; return sends a value back to whoever "
                                "called it. If there is no return, the function returns None. Keep each function "
                                "small and single-purpose — it is far easier to test and to read.",
                                "Parameters with defaults make a function flexible without branching inside it. A "
                                "common beginner bug is a mutable default like items=[]: that list is created once "
                                "and shared across every call, so use None and build a fresh list inside.",
                            ],
                            "bullets": [
                                "Return early for the simple or error cases instead of deep nesting",
                                "A docstring (a string on the first line) documents what the function does",
                                "Keyword arguments call it by name: grade(95, letter=False)",
                            ],
                            "note": "Never write def add(item, bucket=[]) — use bucket=None and set bucket = [] if bucket is None inside.",
                            "estimated_minutes": 12,
                        },
                        {
                            "title": "Comprehensions",
                            "kind": "code",
                            "summary": "One readable line to reshape a list or dict.",
                            "paragraphs": [
                                "A comprehension reads almost like the sentence describing it: 'the scores, for "
                                "each score in scores, if the score is at least 80'. Because it returns a brand new "
                                "collection, the original stays untouched.",
                            ],
                            "code": {
                                "language": "python",
                                "caption": "Filtering and remapping with comprehensions",
                                "code": """scores = [88, 92, 71, 92, 65]
top = [s for s in scores if s >= 80]            # [88, 92, 92]

by_name = {"Ada": 92, "Grace": 88, "Bo": 71}
honours = {name: s for name, s in by_name.items() if s >= 90}  # {"Ada": 92}
print(top)
print(honours)""",
                            },
                            "estimated_minutes": 13,
                        },
                        {
                            "title": "Check your understanding",
                            "kind": "quiz",
                            "summary": "Four questions on functions and comprehensions.",
                            "paragraphs": ["Four questions — the explanations are here to help you learn, not to judge you."],
                            "questions": [
                                {
                                    "prompt": "What does a function return if it has no return statement?",
                                    "choices": ["An empty string", "0", "None", "It raises an error"],
                                    "correct": 2,
                                    "explanation": "Every function returns None implicitly unless you specify a value.",
                                },
                                {
                                    "prompt": "Why is a default argument like items=[] risky?",
                                    "choices": [
                                        "Lists cannot be defaults",
                                        "The same list object is reused across every call",
                                        "It always raises TypeError",
                                        "Defaults must be numbers",
                                    ],
                                    "correct": 1,
                                    "explanation": "The default is created once at definition time, so items leak between calls.",
                                },
                                {
                                    "prompt": "What does [s for s in scores if s >= 80] build?",
                                    "choices": [
                                        "scores, sorted in place",
                                        "A new list holding only the scores of 80 or more",
                                        "The first score that reaches 80",
                                        "An error until scores becomes a dict",
                                    ],
                                    "correct": 1,
                                    "explanation": "The if filters the items and the comprehension returns a brand-new list, so scores itself stays untouched.",
                                },
                                {
                                    "prompt": "Where does a docstring go?",
                                    "choices": [
                                        "On the first line inside the function",
                                        "After the final return statement",
                                        "On the line above def as a comment",
                                        "In a text file beside the module",
                                    ],
                                    "correct": 0,
                                    "explanation": "A docstring is simply the string written on the function's first line, and it documents what the function does.",
                                },
                            ],
                            "estimated_minutes": 5,
                        },
                    ],
                },
            ],
        },
        {
            "title": "Working with Data in Python",
            "subtitle": "Choose the right container, and store results in files and JSON.",
            "level": "intermediate",
            "category": "python",
            "duration_hours": 11,
            "objectives": [
                "Pick between list, dict and set based on how you access data",
                "Read and write files and JSON safely",
                "Set up an isolated environment with venv and pip",
            ],
            "requirements": ["'Python Basics: Values, Logic and Functions' or comfortable functions and loops."],
            "modules": [
                {
                    "title": "Lists, dicts and sets",
                    "summary": "The three containers you touch every day, and how they differ.",
                    "lessons": [
                        {
                            "title": "Choosing a collection",
                            "kind": "text",
                            "summary": "Match the container to how you actually use the data.",
                            "paragraphs": [
                                "A list is ordered and allows duplicates — great for a playlist or a to-do list. "
                                "A dict maps unique keys to values and finds them in roughly constant time, so it "
                                "is the natural choice for lookups by name or id. A set stores unique, unordered "
                                "items and answers 'is this here?' instantly, which makes it perfect for removing "
                                "duplicates.",
                                "dict.get(key, default) returns a fallback instead of raising when a key is "
                                "missing, so you do not have to wrap every read in try/except.",
                            ],
                            "bullets": [
                                "in checks membership: 'Ada' in by_name looks only at keys",
                                "Sets support union, intersection and difference",
                                "Lists and strings are mutable vs immutable respectively: strings never change in place",
                            ],
                            "estimated_minutes": 12,
                        },
                        {
                            "title": "Common operations",
                            "kind": "code",
                            "summary": "Adding, reading and de-duplicating data.",
                            "paragraphs": [
                                "These few lines cover most real-day work: append to a list, build and update a "
                                "dict, and turn a messy list into a clean set of unique values.",
                            ],
                            "code": {
                                "language": "python",
                                "caption": "List, dict and set in one view",
                                "code": """plan = ["HTML", "CSS", "JavaScript"]
plan.append("Python")
print("Python" in plan)                  # True

progress = {"course": "Python", "percent": 40}
progress["percent"] = 55                  # update a value
print(progress.get("mentor", "not assigned"))  # a safe read with a default

tags = ["web", "python", "web", "sql"]
print(sorted(set(tags)))                  # ['python', 'sql', 'web']""",
                            },
                            "estimated_minutes": 14,
                        },
                        {
                            "title": "Check your understanding",
                            "kind": "quiz",
                            "summary": "Four questions on collections.",
                            "paragraphs": ["Four questions to lock in the difference between the containers."],
                            "questions": [
                                {
                                    "prompt": "Which collection guarantees unique, unordered items?",
                                    "choices": ["list", "dict", "set", "tuple"],
                                    "correct": 2,
                                    "explanation": "A set cannot contain duplicates and does not keep an order.",
                                },
                                {
                                    "prompt": "What does d.get('missing', 0) do when the key is absent?",
                                    "choices": ["Raises KeyError", "Returns 0", "Adds the key with value 0", "Returns None always"],
                                    "correct": 1,
                                    "explanation": "get returns the default you passed instead of raising — note it does not insert the key.",
                                },
                                {
                                    "prompt": "What does 'Ada' in by_name check when by_name is a dict?",
                                    "choices": [
                                        "Whether any value equals 'Ada'",
                                        "Whether 'Ada' is a key",
                                        "Whether 'Ada' is inside a nested list",
                                        "Nothing — in only works on lists",
                                    ],
                                    "correct": 1,
                                    "explanation": "Membership testing on a dict looks at the keys only, never at the values.",
                                },
                                {
                                    "prompt": "What does sorted(set(tags)) print for tags = ['web', 'python', 'web', 'sql']?",
                                    "choices": [
                                        "['web', 'python', 'web', 'sql']",
                                        "['python', 'sql', 'web']",
                                        "['web', 'python', 'sql']",
                                        "The set, with no sorting at all",
                                    ],
                                    "correct": 1,
                                    "explanation": "set() drops the repeated 'web' because a set holds unique items, and sorted() returns what is left in order.",
                                },
                            ],
                            "estimated_minutes": 5,
                        },
                    ],
                },
                {
                    "title": "Files, JSON and your environment",
                    "summary": "Persist results and keep each project's dependencies tidy.",
                    "lessons": [
                        {
                            "title": "Files, JSON, venv and pip",
                            "kind": "text",
                            "summary": "Save real output and run code in an isolated environment.",
                            "paragraphs": [
                                "Files are opened with a path and a mode: 'r' read, 'w' write (which truncates), "
                                "'a' append. Always open inside a with block so the file closes automatically even "
                                "if an error is raised. The json module turns a Python dict into JSON text with "
                                "json.dumps and back again with json.loads.",
                                "Every project deserves its own virtual environment so its packages do not clash "
                                "with anyone else's. Create one with python -m venv .venv, activate it, and record "
                                "what you installed with pip freeze > requirements.txt so a teammate can rebuild it "
                                "exactly.",
                            ],
                            "bullets": [
                                "python -m venv .venv  # make the environment",
                                "source .venv/bin/activate  # on Windows: .venv\\Scripts\\activate",
                                "pip install requests   # add a package to this project only",
                                "Always pass encoding='utf-8' so behaviour does not depend on the operating system",
                            ],
                            "estimated_minutes": 13,
                        },
                        {
                            "title": "Reading and writing JSON",
                            "kind": "code",
                            "summary": "Round-trip a progress record through a file.",
                            "paragraphs": [
                                "This is the pattern you will reuse constantly: load a JSON file if it exists, "
                                "change a value, and write it back out nicely formatted.",
                            ],
                            "code": {
                                "language": "python",
                                "caption": "Load, bump and save a progress file",
                                "code": """import json
from pathlib import Path

record = Path("progress.json")

if record.exists():
    data = json.loads(record.read_text(encoding="utf-8"))
else:
    data = {"streak": 0}

data["streak"] += 1
record.write_text(json.dumps(data, indent=2), encoding="utf-8")
print(json.dumps(data))                    # {"streak": 1}""",
                            },
                            "note": "json.dump (no s) writes to an open file; json.dumps (with s) returns a string. Mixing them up is a classic first bug.",
                            "estimated_minutes": 15,
                        },
                        {
                            "title": "Check your understanding",
                            "kind": "quiz",
                            "summary": "Four questions on files, JSON and environments.",
                            "paragraphs": ["Four questions on the everyday habits that keep your project clean."],
                            "questions": [
                                {
                                    "prompt": "Why open a file inside a 'with' block?",
                                    "choices": [
                                        "It is faster",
                                        "The file is closed automatically even if an error occurs",
                                        "open() is deprecated",
                                        "It loads the whole file into memory",
                                    ],
                                    "correct": 1,
                                    "explanation": "The context manager guarantees cleanup on every exit path.",
                                },
                                {
                                    "prompt": "What does pip freeze > requirements.txt give you?",
                                    "choices": [
                                        "A list of every Python file on the computer",
                                        "The exact packages and versions installed, so the environment is reproducible",
                                        "A backup of your data",
                                        "A way to delete a virtual environment",
                                    ],
                                    "correct": 1,
                                    "explanation": "It pins your dependencies so anyone can rebuild the same environment.",
                                },
                                {
                                    "prompt": "What happens if you open an existing file in mode 'w'?",
                                    "choices": [
                                        "The new text is appended to the end",
                                        "The existing contents are truncated",
                                        "Python raises an error",
                                        "The file opens read-only",
                                    ],
                                    "correct": 1,
                                    "explanation": "Mode 'w' writes from the start and erases what was already there; use 'a' when you want to append.",
                                },
                                {
                                    "prompt": "Which call turns a Python dict into JSON text?",
                                    "choices": ["json.loads", "json.dumps", "json.read", "json.encode"],
                                    "correct": 1,
                                    "explanation": "json.dumps returns a string, while json.loads goes the other way and parses JSON text back into data.",
                                },
                            ],
                            "estimated_minutes": 5,
                        },
                    ],
                },
            ],
        },
    ],
}

DJANGO = {
    "title": "Django Backend Development",
    "slug": "django-backend-development",
    "level": "beginner",
    "color": "#059669",
    "icon": "Server",
    "description": "Build the server side of a real product. You will model data, hand Django the schema, then "
    "serve clean JSON with Django REST Framework — using Django 5+ conventions.",
    "courses": [
        {
            "title": "Models, Migrations and the Admin",
            "subtitle": "Turn a model class into a database table and manage it without writing SQL.",
            "level": "beginner",
            "category": "backend",
            "duration_hours": 12,
            "objectives": [
                "Define models and let the ORM generate and run migrations",
                "Query the database through the ORM",
                "Register models in the built-in admin site",
            ],
            "requirements": ["Comfortable with Python classes, or the 'Python Programming' path."],
            "modules": [
                {
                    "title": "Models and the ORM",
                    "summary": "Your models are the single source of truth for the database structure.",
                    "lessons": [
                        {
                            "title": "How Django is organised",
                            "kind": "text",
                            "summary": "Models own data, views own logic, templates own presentation.",
                            "paragraphs": [
                                "Django is a full-stack framework: it gives you an ORM for data, a URL router, a "
                                "view layer, a template engine and a ready-made admin, all with sensible defaults. "
                                "A settings.py file wires everything together, and each feature lives in an app "
                                "listed in INSTALLED_APPS.",
                                "The ORM (object-relational mapper) lets you write Python instead of SQL. You define "
                                "a model class with fields; each field becomes a column in a database table. Query "
                                "sets are lazy — nothing touches the database until you iterate over the results.",
                            ],
                            "bullets": [
                                "A model class maps to a table; an instance maps to a row",
                                "CharField needs max_length; ForeignKey needs on_delete",
                                "__str__ controls how the object is shown in the admin",
                            ],
                            "estimated_minutes": 13,
                        },
                        {
                            "title": "A model and its fields",
                            "kind": "code",
                            "summary": "Define the shape of your data once, in Python.",
                            "paragraphs": [
                                "ForeignKey connects a lesson to its course. on_delete=CASCADE means deleting a "
                                "course removes its lessons too; related_name gives you the reverse lookup "
                                "course.lessons. Meta.ordering sets the default order for query sets.",
                            ],
                            "code": {
                                "language": "django",
                                "caption": "learning/models.py",
                                "code": """from django.db import models

class Course(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    duration_hours = models.PositiveIntegerField(default=4)

    class Meta:
        ordering = ("-duration_hours",)

    def __str__(self):
        return self.title

class Lesson(models.Model):
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="lessons"
    )
    title = models.CharField(max_length=220)""",
                            },
                            "estimated_minutes": 15,
                        },
                        {
                            "title": "Check your understanding",
                            "kind": "quiz",
                            "summary": "Four questions on models and the ORM.",
                            "paragraphs": ["Four questions before moving on — take your time and reread if needed."],
                            "questions": [
                                {
                                    "prompt": "What does a Django model class correspond to?",
                                    "choices": ["A template", "A database table", "A URL", "A form widget"],
                                    "correct": 1,
                                    "explanation": "Each model becomes one table; each field becomes one column.",
                                },
                                {
                                    "prompt": "What does on_delete=models.CASCADE do?",
                                    "choices": [
                                        "Deletes the related course when a lesson is deleted",
                                        "Deletes the child rows when the parent is deleted",
                                        "Refuses to delete anything",
                                        "Sets the field to NULL",
                                    ],
                                    "correct": 1,
                                    "explanation": "CASCADE removes dependent rows (lessons) when the referenced object (course) is deleted.",
                                },
                                {
                                    "prompt": "Which option must you always give a CharField?",
                                    "choices": ["max_length", "unique", "null", "default"],
                                    "correct": 0,
                                    "explanation": "CharField requires max_length, which is how Django knows how much text the column may hold.",
                                },
                                {
                                    "prompt": "What does a model's __str__ method control?",
                                    "choices": [
                                        "The name of the database table",
                                        "How the object is shown in the admin",
                                        "Which fields may be edited",
                                        "The URL of the record",
                                    ],
                                    "correct": 1,
                                    "explanation": "Django calls __str__ to get a readable label for each instance, and that is what the admin displays.",
                                },
                            ],
                            "estimated_minutes": 5,
                        },
                    ],
                },
                {
                    "title": "Migrations and the admin site",
                    "summary": "Apply schema changes safely and give your team a management UI.",
                    "lessons": [
                        {
                            "title": "Migrations and makemigrations",
                            "kind": "text",
                            "summary": "Django turns model edits into ordered, versioned schema changes.",
                            "paragraphs": [
                                "You never edit the database by hand. Change a model, run python manage.py "
                                "makemigrations to write a migration file describing the change, then run python "
                                "manage.py migrate to apply it. Migrations are real code, so they belong in version "
                                "control and replay in a fixed order on every environment.",
                                "The admin site is generated from your models for free. Register a model and, with "
                                "a small ModelAdmin, choose which columns show in the list and which fields are "
                                "searchable — no HTML required.",
                            ],
                            "bullets": [
                                "python manage.py makemigrations   # record the change",
                                "python manage.py migrate           # apply it to the database",
                                "Admin is for trusted staff, not the public — keep it secure",
                            ],
                            "estimated_minutes": 12,
                        },
                        {
                            "title": "Admin registration and a query set",
                            "kind": "code",
                            "summary": "Configure the admin, then read the same data from code.",
                            "paragraphs": [
                                "Below, the admin shows the title, slug and hours with a search box. The last "
                                "lines use the ORM directly: filter and order_by build a query set that becomes "
                                "SQL only when you evaluate it.",
                            ],
                            "code": {
                                "language": "django",
                                "caption": "learning/admin.py and a shell query",
                                "code": """from django.contrib import admin
from .models import Course

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "duration_hours")
    search_fields = ("title", "slug")

# In a view or 'python manage.py shell', query through the ORM:
long_courses = Course.objects.filter(duration_hours__gte=8).order_by("title")
for course in long_courses:
    print(course.title, course.lessons.count())""",
                            },
                            "note": "The double underscore means a lookup or a relationship: duration_hours__gte is 'greater than or equal', course__title reaches through a relation.",
                            "estimated_minutes": 14,
                        },
                        {
                            "title": "Check your understanding",
                            "kind": "quiz",
                            "summary": "Four questions on migrations and the admin.",
                            "paragraphs": ["Four questions on the two commands and the config you just met."],
                            "questions": [
                                {
                                    "prompt": "What is the correct order when a model changes?",
                                    "choices": [
                                        "migrate then makemigrations",
                                        "makemigrations then migrate",
                                        "Just restart the server",
                                        "Edit the table directly in SQL",
                                    ],
                                    "correct": 1,
                                    "explanation": "makemigrations writes the change file; migrate applies it to the database.",
                                },
                                {
                                    "prompt": "When does filter(...) actually hit the database?",
                                    "choices": [
                                        "Immediately, as soon as you call it",
                                        "Only when the query set is evaluated (iterated or sliced)",
                                        "Never",
                                        "Only after migrate",
                                    ],
                                    "correct": 1,
                                    "explanation": "Query sets are lazy, so conditions can be chained before one round trip.",
                                },
                                {
                                    "prompt": "What does Course.objects.filter(duration_hours__gte=8) select?",
                                    "choices": [
                                        "Courses of exactly 8 hours",
                                        "Courses of 8 hours or more",
                                        "Courses shorter than 8 hours",
                                        "The 8 longest courses",
                                    ],
                                    "correct": 1,
                                    "explanation": "The __gte lookup means greater than or equal, so a course of exactly 8 hours is included.",
                                },
                                {
                                    "prompt": "Which ModelAdmin attribute chooses the columns shown in the admin list?",
                                    "choices": ["search_fields", "list_display", "fields", "ordering"],
                                    "correct": 1,
                                    "explanation": "list_display names the columns for each row; search_fields only powers the search box at the top.",
                                },
                            ],
                            "estimated_minutes": 5,
                        },
                    ],
                },
            ],
        },
        {
            "title": "Django REST Framework APIs",
            "subtitle": "Expose your data as JSON and control who is allowed in.",
            "level": "intermediate",
            "category": "backend",
            "duration_hours": 12,
            "objectives": [
                "Turn a model into endpoints with a serializer and a view set",
                "Return correct HTTP status codes",
                "Protect endpoints with authentication and permissions",
            ],
            "requirements": ["'Models, Migrations and the Admin' or comfortable with Django models."],
            "modules": [
                {
                    "title": "Serializers and view sets",
                    "summary": "The two pieces that turn a model into a full CRUD API.",
                    "lessons": [
                        {
                            "title": "What DRF does",
                            "kind": "text",
                            "summary": "A serializer is the bridge between models and JSON.",
                            "paragraphs": [
                                "Django REST Framework (DRF) builds APIs quickly. A serializer converts a model "
                                "instance to JSON and, going the other way, validates incoming data before saving. "
                                "A view set bundles the standard list, retrieve, create, update and delete actions "
                                "into one class, and a router writes the URL patterns for you.",
                                "REST treats your data as resources named by URLs: /api/courses/ is a collection, "
                                "/api/courses/42/ is a single item. The HTTP verb expresses the action you want.",
                            ],
                            "bullets": [
                                "GET reads, POST creates, PUT replaces, PATCH partially updates, DELETE removes",
                                "A ModelSerializer maps to a model with a Meta class",
                                "Always list fields explicitly — never rely on '__all__' in production",
                            ],
                            "estimated_minutes": 12,
                        },
                        {
                            "title": "A serializer and a view set",
                            "kind": "code",
                            "summary": "One class produces list/create/update/delete endpoints.",
                            "paragraphs": [
                                "The view set names a query set and a serializer; the router turns the view set "
                                "into URLs. Registering 'courses' yields /api/courses/ for listing and creating, "
                                "and /api/courses/<id>/ for reading, updating or deleting a single course.",
                            ],
                            "code": {
                                "language": "django",
                                "caption": "learning/api.py",
                                "code": """from rest_framework import serializers, viewsets, routers
from .models import Course

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ["id", "title", "slug", "duration_hours"]

class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer

router = routers.DefaultRouter()
router.register("courses", CourseViewSet, basename="course")
# urls.py: urlpatterns = [path("api/", include(router.urls))]""",
                            },
                            "estimated_minutes": 15,
                        },
                        {
                            "title": "Check your understanding",
                            "kind": "quiz",
                            "summary": "Four questions on serializers and view sets.",
                            "paragraphs": ["Four questions on the pieces that make the API."],
                            "questions": [
                                {
                                    "prompt": "Which HTTP verb creates a new resource?",
                                    "choices": ["GET", "POST", "DELETE", "HEAD"],
                                    "correct": 1,
                                    "explanation": "POST to a collection URL creates an item and returns 201 Created.",
                                },
                                {
                                    "prompt": "What is a serializer's job?",
                                    "choices": [
                                        "Only rendering HTML pages",
                                        "Converting model data to JSON and validating incoming data",
                                        "Managing database migrations",
                                        "Styling the admin",
                                    ],
                                    "correct": 1,
                                    "explanation": "Serializers are the two-way bridge between the ORM and JSON.",
                                },
                                {
                                    "prompt": "What does a DRF router give you?",
                                    "choices": [
                                        "The URL patterns for a view set",
                                        "The SQL behind a query set",
                                        "The template for the API page",
                                        "The migration for a model",
                                    ],
                                    "correct": 0,
                                    "explanation": "Registering a view set with a router writes the URLs for you, yielding the collection and the single-item paths.",
                                },
                                {
                                    "prompt": "How does PATCH differ from PUT?",
                                    "choices": [
                                        "PATCH replaces the whole resource, PUT changes one field",
                                        "PATCH updates only the fields you send, PUT replaces the resource",
                                        "They are two names for the same action",
                                        "PATCH reads a resource, PUT writes it",
                                    ],
                                    "correct": 1,
                                    "explanation": "PUT replaces the resource, while PATCH partially updates just the parts named in the body.",
                                },
                            ],
                            "estimated_minutes": 5,
                        },
                    ],
                },
                {
                    "title": "Authentication and permissions",
                    "summary": "Decide who is calling and what they are allowed to do.",
                    "lessons": [
                        {
                            "title": "Who may access your API",
                            "kind": "text",
                            "summary": "Authentication proves identity; permissions grant ability.",
                            "paragraphs": [
                                "These are two separate steps. Authentication answers 'who are you?' (session "
                                "cookies, a token, or JWT), while permission answers 'are you allowed to do this "
                                "action?'. In DRF you set both per view or as project-wide defaults in settings.",
                                "JSON Web Tokens (JWT) are compact, signed tokens you send in an Authorization "
                                "header. Keep access tokens short-lived and pair them with a refresh token. Never "
                                "put a secret in a token — the signature only proves it was not tampered with.",
                            ],
                            "bullets": [
                                "IsAuthenticatedOrReadOnly: anyone can GET, only signed-in users can write",
                                "Set defaults once in REST_FRAMEWORK so every view behaves the same",
                                "401 means not authenticated; 403 means authenticated but not allowed",
                            ],
                            "estimated_minutes": 12,
                        },
                        {
                            "title": "Locking down a view set",
                            "kind": "code",
                            "summary": "Require a valid JWT and only allow writes for signed-in users.",
                            "paragraphs": [
                                "Here a single view set declares its authentication and permission classes, and "
                                "the settings block makes JWT the project default so new endpoints inherit it "
                                "automatically.",
                            ],
                            "code": {
                                "language": "django",
                                "caption": "Per-view config plus project defaults",
                                "code": """from rest_framework import viewsets, permissions
from rest_framework_simplejwt.authentication import JWTAuthentication

class EnrolledLessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

# settings.py
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
}""",
                            },
                            "note": "IsAuthenticatedOrReadOnly lets the public read your catalogue but keeps the write actions for logged-in members.",
                            "estimated_minutes": 14,
                        },
                        {
                            "title": "Check your understanding",
                            "kind": "quiz",
                            "summary": "Four questions on authentication and permissions.",
                            "paragraphs": ["Four questions to make sure the distinction is clear."],
                            "questions": [
                                {
                                    "prompt": "A logged-in user tries an action their role forbids. Which status fits?",
                                    "choices": ["401 Unauthorized", "403 Forbidden", "404 Not Found", "200 OK"],
                                    "correct": 1,
                                    "explanation": "403 means identity is known but the action is not permitted; 401 means not authenticated.",
                                },
                                {
                                    "prompt": "Which class allows anyone to read but only signed-in users to write?",
                                    "choices": ["AllowAny", "IsAuthenticated", "IsAuthenticatedOrReadOnly", "AdminOnly"],
                                    "correct": 2,
                                    "explanation": "IsAuthenticatedOrReadOnly is exactly read-open, write-guarded.",
                                },
                                {
                                    "prompt": "Which step answers the question 'who are you?'",
                                    "choices": ["Permission classes", "Authentication", "Serialization", "Pagination"],
                                    "correct": 1,
                                    "explanation": "Authentication identifies the caller with a session, token or JWT; permissions then decide what that caller may do.",
                                },
                                {
                                    "prompt": "Where do you set authentication and permissions once for every endpoint?",
                                    "choices": [
                                        "In each serializer's Meta class",
                                        "In the REST_FRAMEWORK dict in settings.py",
                                        "In the admin registration for the model",
                                        "At the bottom of the migration file",
                                    ],
                                    "correct": 1,
                                    "explanation": "The DEFAULT_AUTHENTICATION_CLASSES and DEFAULT_PERMISSION_CLASSES entries there make each new view inherit the same behaviour.",
                                },
                            ],
                            "estimated_minutes": 5,
                        },
                    ],
                },
            ],
        },
    ],
}

MYSQL = {
    "title": "MySQL and Database Design",
    "slug": "mysql-and-database-design",
    "level": "beginner",
    "color": "#0ea5e9",
    "icon": "Database",
    "description": "Ask a database for exactly what you need, then design schemas that stay honest as rows pile "
    "up. Every example targets MySQL 8.",
    "courses": [
        {
            "title": "Querying Data with SQL",
            "subtitle": "Read, filter, join and aggregate — the language that talks to your data.",
            "level": "beginner",
            "category": "databases",
            "duration_hours": 10,
            "objectives": [
                "Select, filter and order rows",
                "Combine tables with joins",
                "Summarise groups with aggregates and HAVING",
            ],
            "requirements": ["A MySQL 8 server (or a hosted instance) and any client. No SQL assumed."],
            "modules": [
                {
                    "title": "SELECT, WHERE and ORDER BY",
                    "summary": "The shape of the query you will write a hundred times.",
                    "lessons": [
                        {
                            "title": "Relational basics",
                            "kind": "text",
                            "summary": "A table is rows crossed with columns; SQL describes the result you want.",
                            "paragraphs": [
                                "SQL is declarative: you say which rows and columns you want, and the engine "
                                "decides how to fetch them. SELECT names the columns, FROM the table, and WHERE "
                                "the rows to keep. ORDER BY sorts, and LIMIT caps the count.",
                                "One idea trips up every beginner: NULL means unknown, and unknown never equals "
                                "anything. Test it with IS NULL or IS NOT NULL, never = NULL. Also, an empty "
                                "string is a real value, not the same as NULL.",
                            ],
                            "bullets": [
                                "Statements usually end with a semicolon",
                                "Single quotes are for text; backticks quote an identifier if it clashes with a keyword",
                                "-- starts a comment",
                            ],
                            "estimated_minutes": 11,
                        },
                        {
                            "title": "Selecting and filtering",
                            "kind": "code",
                            "summary": "Pick columns, keep matching rows, sort and page.",
                            "paragraphs": [
                                "This is the everyday query. Notice the exclusive logic in the filter and how "
                                "ORDER BY runs before LIMIT so paging is predictable.",
                            ],
                            "code": {
                                "language": "sql",
                                "caption": "The query you will write most often",
                                "code": """SELECT title, duration_hours
FROM courses
WHERE level = 'beginner'
  AND duration_hours BETWEEN 4 AND 12
ORDER BY duration_hours DESC, title ASC
LIMIT 10;""",
                            },
                            "note": "BETWEEN is inclusive at both ends, so 4 AND 12 includes 4 and 12.",
                            "estimated_minutes": 13,
                        },
                        {
                            "title": "Check your understanding",
                            "kind": "quiz",
                            "summary": "Four questions on selecting and filtering.",
                            "paragraphs": ["Four questions on the basics before we join tables."],
                            "questions": [
                                {
                                    "prompt": "How do you find rows where a column has no value?",
                                    "choices": ["col = NULL", "col IS NULL", "col == NULL", "col = ''"],
                                    "correct": 1,
                                    "explanation": "NULL is unknown, so it is tested with IS NULL, never with =.",
                                },
                                {
                                    "prompt": "What does ORDER BY duration_hours DESC do?",
                                    "choices": [
                                        "Sorts from smallest to largest",
                                        "Sorts from largest to smallest",
                                        "Filters out large values",
                                        "Counts the rows",
                                    ],
                                    "correct": 1,
                                    "explanation": "DESC means descending — biggest values first.",
                                },
                                {
                                    "prompt": "Does WHERE duration_hours BETWEEN 4 AND 12 keep a course of exactly 12 hours?",
                                    "choices": [
                                        "No, the upper bound is exclusive",
                                        "Yes, BETWEEN is inclusive at both ends",
                                        "Only when 12 is also the lower bound",
                                        "It depends on the column type",
                                    ],
                                    "correct": 1,
                                    "explanation": "BETWEEN includes both boundary values, so 4 and 12 are both kept.",
                                },
                                {
                                    "prompt": "When do you wrap a name in backticks in MySQL?",
                                    "choices": [
                                        "When writing a text value",
                                        "When an identifier clashes with a keyword",
                                        "When ending a statement",
                                        "When starting a comment",
                                    ],
                                    "correct": 1,
                                    "explanation": "Backticks quote an identifier; single quotes are what you use around text values.",
                                },
                            ],
                            "estimated_minutes": 5,
                        },
                    ],
                },
                {
                    "title": "JOIN and aggregates",
                    "summary": "Stitch tables together and collapse rows into one value per group.",
                    "lessons": [
                        {
                            "title": "Joins and grouping",
                            "kind": "text",
                            "summary": "Relational power comes from combining tables and summarising them.",
                            "paragraphs": [
                                "A JOIN connects rows across tables using related columns — lessons point at a "
                                "course through course_id. INNER JOIN keeps only rows that match on both sides; "
                                "LEFT JOIN keeps every left row, filling NULL when there is no match, which is how "
                                "you find a course with zero lessons.",
                                "Aggregate functions like COUNT, SUM, AVG, MIN and MAX fold many rows into one "
                                "value per group. GROUP BY defines the groups; HAVING filters groups after they "
                                "are formed, which is why an aggregate cannot go in WHERE.",
                            ],
                            "bullets": [
                                "WHERE filters rows before grouping; HAVING filters after",
                                "COUNT(*) counts rows; COUNT(column) ignores NULLs",
                                "Every non-aggregated column in SELECT must appear in GROUP BY",
                            ],
                            "estimated_minutes": 13,
                        },
                        {
                            "title": "A join with a count",
                            "kind": "code",
                            "summary": "One statement lists courses that have at least three lessons.",
                            "paragraphs": [
                                "Here each course is joined to its lessons, grouped by the course, and COUNT turns "
                                "each group into a single number. HAVING then keeps only the well-populated "
                                "courses.",
                            ],
                            "code": {
                                "language": "sql",
                                "caption": "Count lessons per course",
                                "code": """SELECT c.title, COUNT(l.id) AS lesson_count
FROM courses c
JOIN lessons l ON l.course_id = c.id
GROUP BY c.id, c.title
HAVING COUNT(l.id) >= 3
ORDER BY lesson_count DESC;""",
                            },
                            "estimated_minutes": 14,
                        },
                        {
                            "title": "Check your understanding",
                            "kind": "quiz",
                            "summary": "Four questions on joins and grouping.",
                            "paragraphs": ["Four questions on combining tables and summarising them."],
                            "questions": [
                                {
                                    "prompt": "Which join keeps every course even if it has no lessons?",
                                    "choices": ["INNER JOIN", "LEFT JOIN", "CROSS JOIN", "No join"],
                                    "correct": 1,
                                    "explanation": "LEFT JOIN keeps all left-table rows, with NULLs where the right side is missing.",
                                },
                                {
                                    "prompt": "Where must an aggregate condition like COUNT(*) >= 3 go?",
                                    "choices": ["WHERE", "HAVING", "ORDER BY", "LIMIT"],
                                    "correct": 1,
                                    "explanation": "HAVING runs after GROUP BY, so it can reference aggregates.",
                                },
                                {
                                    "prompt": "What is the difference between COUNT(*) and COUNT(column)?",
                                    "choices": [
                                        "There is none, the two always match",
                                        "COUNT(*) counts rows, COUNT(column) ignores NULLs",
                                        "COUNT(column) includes the NULLs as well",
                                        "COUNT(*) only works without a JOIN",
                                    ],
                                    "correct": 1,
                                    "explanation": "The star counts every row in the group, while the column form skips rows where that column is NULL.",
                                },
                                {
                                    "prompt": "Why are c.id and c.title listed in GROUP BY in the lesson's query?",
                                    "choices": [
                                        "GROUP BY must name every table in FROM",
                                        "Every non-aggregated column in SELECT has to be grouped",
                                        "They are the primary key of the lessons table",
                                        "It makes COUNT(l.id) run faster",
                                    ],
                                    "correct": 1,
                                    "explanation": "The grouping is defined by those columns, so anything else you select must either be grouped or sit inside an aggregate.",
                                },
                            ],
                            "estimated_minutes": 5,
                        },
                    ],
                },
            ],
        },
        {
            "title": "Schema Design and Integrity",
            "subtitle": "Model data so it cannot lie, and make queries use indexes.",
            "level": "intermediate",
            "category": "databases",
            "duration_hours": 11,
            "objectives": [
                "Define tables with primary keys, foreign keys and constraints",
                "Explain why normalization avoids duplicate facts",
                "Add an index that the query optimiser actually uses",
            ],
            "requirements": ["'Querying Data with SQL' or comfortable with joins and grouping."],
            "modules": [
                {
                    "title": "Keys and constraints",
                    "summary": "Let the database enforce the rules, not just your code.",
                    "lessons": [
                        {
                            "title": "Types, keys and constraints",
                            "kind": "text",
                            "summary": "The right type and the right key are your first two integrity checks.",
                            "paragraphs": [
                                "Match the type to the meaning: use DECIMAL, not FLOAT, for money, because binary "
                                "floats cannot hold 0.10 exactly. A primary key uniquely identifies each row and is "
                                "usually an AUTO_INCREMENT integer. A UNIQUE index stops duplicate values, like "
                                "two courses sharing a slug.",
                                "A foreign key guarantees that a lesson's course_id points at a real course, and "
                                "ON DELETE decides what happens to the lessons when the course goes. NOT NULL "
                                "refuses empty values at write time, so bad data never enters the table.",
                            ],
                            "bullets": [
                                "Primary key: unique and never NULL",
                                "Foreign key: must reference an existing key in another table",
                                "UNSIGNED stops negative counts your app would have to guard against",
                            ],
                            "estimated_minutes": 13,
                        },
                        {
                            "title": "Two related tables",
                            "kind": "code",
                            "summary": "Create a parent and a child linked by a foreign key.",
                            "paragraphs": [
                                "The child table references the parent through course_id. Deleting a course "
                                "cascades to its lessons, and the unique slug prevents clashes.",
                            ],
                            "code": {
                                "language": "sql",
                                "caption": "A parent-child schema",
                                "code": """CREATE TABLE courses (
  id    INT UNSIGNED NOT NULL AUTO_INCREMENT,
  title VARCHAR(200) NOT NULL,
  slug  VARCHAR(220) NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_course_slug (slug)
);

CREATE TABLE lessons (
  id        INT UNSIGNED NOT NULL AUTO_INCREMENT,
  course_id INT UNSIGNED NOT NULL,
  title     VARCHAR(220) NOT NULL,
  PRIMARY KEY (id),
  CONSTRAINT fk_lesson_course FOREIGN KEY (course_id)
    REFERENCES courses (id) ON DELETE CASCADE
);""",
                            },
                            "estimated_minutes": 15,
                        },
                        {
                            "title": "Check your understanding",
                            "kind": "quiz",
                            "summary": "Four questions on keys and constraints.",
                            "paragraphs": ["Four questions on the rules the database enforces for you."],
                            "questions": [
                                {
                                    "prompt": "Which type should store a price?",
                                    "choices": ["FLOAT", "DOUBLE", "DECIMAL", "VARCHAR"],
                                    "correct": 2,
                                    "explanation": "DECIMAL holds exact base-10 values; FLOAT rounds and corrupts money math.",
                                },
                                {
                                    "prompt": "What does a FOREIGN KEY guarantee?",
                                    "choices": [
                                        "Values are unique",
                                        "Each value points at a real row in another table",
                                        "The column cannot be NULL",
                                        "The column is indexed only on reads",
                                    ],
                                    "correct": 1,
                                    "explanation": "It enforces referential integrity so orphan references are rejected.",
                                },
                                {
                                    "prompt": "Which constraint stops two courses from sharing the same slug?",
                                    "choices": ["PRIMARY KEY", "UNIQUE", "AUTO_INCREMENT", "FOREIGN KEY"],
                                    "correct": 1,
                                    "explanation": "A UNIQUE index rejects a repeated value in that column, which is exactly what uq_course_slug does.",
                                },
                                {
                                    "prompt": "What does NOT NULL do?",
                                    "choices": [
                                        "Gives the column a default value",
                                        "Rejects any write that leaves the column empty",
                                        "Makes the value unique across rows",
                                        "Deletes rows that have no value",
                                    ],
                                    "correct": 1,
                                    "explanation": "It is checked at write time, so empty values never enter the table in the first place.",
                                },
                            ],
                            "estimated_minutes": 5,
                        },
                    ],
                },
                {
                    "title": "Indexes and normalization",
                    "summary": "Speed up lookups and remove duplicated facts.",
                    "lessons": [
                        {
                            "title": "Indexes and normal forms",
                            "kind": "text",
                            "summary": "An index is an ordered roadmap; normalization splits facts cleanly.",
                            "paragraphs": [
                                "A B-tree index speeds up lookups on its leading column and costs a little on every "
                                "write, so keep indexes few and intentional. A foreign key column you filter by is a "
                                "prime candidate for an index. To see whether MySQL uses it, prefix a query with "
                                "EXPLAIN and look for a chosen key instead of a full scan.",
                                "Normalization means each fact lives in exactly one place. First normal form removes "
                                "repeating groups; the others pull out columns that depend on something other than "
                                "the key. Moving course categories into their own table means renaming a category "
                                "is one update, not one per course.",
                            ],
                            "bullets": [
                                "Index the columns you filter and order by — and no more",
                                "A composite index (a, b) helps queries on a, or a then b, but not b alone",
                                "Redundant data invites contradictions; one fact, one place",
                            ],
                            "estimated_minutes": 13,
                        },
                        {
                            "title": "Adding an index and a category table",
                            "kind": "code",
                            "summary": "Index a foreign key and pull categories into their own table.",
                            "paragraphs": [
                                "The CREATE INDEX speeds up the common 'find all lessons for a course'. The second "
                                "block replaces a repeated text column with a reference to a single categories row — "
                                "the essence of normalization.",
                            ],
                            "code": {
                                "language": "sql",
                                "caption": "An index and a normalized lookup table",
                                "code": """CREATE INDEX idx_lessons_course ON lessons (course_id);

CREATE TABLE categories (
  id   INT UNSIGNED NOT NULL AUTO_INCREMENT,
  name VARCHAR(60) NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_category_name (name)
);

ALTER TABLE courses
  ADD COLUMN category_id INT UNSIGNED NOT NULL,
  ADD CONSTRAINT fk_course_category FOREIGN KEY (category_id)
    REFERENCES categories (id);""",
                            },
                            "note": "Adding a column that is NOT NULL to a populated table needs a default or a follow-up UPDATE; do it in two steps in production.",
                            "estimated_minutes": 14,
                        },
                        {
                            "title": "Check your understanding",
                            "kind": "quiz",
                            "summary": "Four questions on indexes and normalization.",
                            "paragraphs": ["Four questions to wrap up the design path."],
                            "questions": [
                                {
                                    "prompt": "Why add an index on a foreign key column?",
                                    "choices": [
                                        "It makes the column unique",
                                        "It speeds up joins and lookups by that column",
                                        "It encrypts the data",
                                        "It removes the need for a primary key",
                                    ],
                                    "correct": 1,
                                    "explanation": "Indexes are ordered structures that avoid scanning the whole table.",
                                },
                                {
                                    "prompt": "What is the goal of normalization?",
                                    "choices": [
                                        "Store every fact once to avoid duplication and contradictions",
                                        "Combine everything into one giant table",
                                        "Remove all foreign keys",
                                        "Make every column nullable",
                                    ],
                                    "correct": 0,
                                    "explanation": "Splitting facts into separate tables keeps updates consistent in one place.",
                                },
                                {
                                    "prompt": "How do you check whether MySQL actually uses an index for a query?",
                                    "choices": [
                                        "Rename the index and run the query again",
                                        "Count the rows with SELECT COUNT(*)",
                                        "Put EXPLAIN in front of the query and look for a chosen key",
                                        "Check that the index name starts with idx_",
                                    ],
                                    "correct": 2,
                                    "explanation": "EXPLAIN prints the plan the optimiser chose, so you can see a key in use instead of a full table scan.",
                                },
                                {
                                    "prompt": "Which lookup can a composite index on (a, b) NOT speed up?",
                                    "choices": ["Filtering by a", "Filtering by a and then b", "Filtering by b alone", "Ordering by a"],
                                    "correct": 2,
                                    "explanation": "The index is ordered by its leading column, so it serves a, or a then b, but a search on b alone cannot use it.",
                                },
                            ],
                            "estimated_minutes": 5,
                        },
                    ],
                },
            ],
        },
    ],
}
