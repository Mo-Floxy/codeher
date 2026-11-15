"""Demonstration community content.

Everything here is labelled as sample data on screen. These are real database
rows — the landing-page counters and leaderboards read them with the same
queries they use for member content — but the accounts themselves are fictional
demonstrations created by `manage.py seed`, not real people.
"""

# Password for every sample account below. The three primary demo logins are also
# listed in the frontend sign-in page; keep them in sync.
DEMO_PASSWORD = "CodeHer!Sample2026"

PEOPLE = {
    "ada": {
        "email": "ada@codeher.dev",
        "username": "ada",
        "display_name": "Ada (sample learner)",
        "role": "learner",
        "password": "CodeHer!Learn2026",
        "headline": "Career switcher learning full-stack, one lesson at a time",
        "bio": "Sample account created by `manage.py seed`. I came from a nursing background and I am "
        "rebuilding my working life around software. Mostly here for the React and Django paths.",
        "interests": ["react", "django", "careers"],
        "learning_technologies": ["JavaScript", "React", "Python", "MySQL"],
        "skill_level": "beginner",
        "country": "Kenya",
        "timezone_name": "Africa/Nairobi",
        "weekly_goal_minutes": 120,
    },
    "grace": {
        "email": "grace@codeher.dev",
        "username": "grace",
        "display_name": "Grace (sample mentor)",
        "role": "mentor",
        "password": "CodeHer!Mentor2026",
        "headline": "Senior backend engineer · mentoring career switchers",
        "bio": "Sample mentor account created by `manage.py seed`. Twelve years building APIs, six of them "
        "mentoring people moving into tech from other fields.",
        "interests": ["django", "system design", "interviews"],
        "learning_technologies": ["Python", "Django", "MySQL"],
        "skill_level": "advanced",
        "country": "United Kingdom",
        "timezone_name": "Europe/London",
        "weekly_goal_minutes": 60,
    },
    "admin": {
        "email": "admin@codeher.dev",
        "username": "admin",
        "display_name": "CodeHer Admin",
        "role": "admin",
        "password": "CodeHer!Admin2026",
        "headline": "Platform administration",
        "bio": "Administrative account created by `manage.py seed`. Use it to reach the admin console.",
        "interests": ["moderation"],
        "learning_technologies": [],
        "skill_level": "advanced",
        "country": "United States",
        "timezone_name": "America/New_York",
        "weekly_goal_minutes": 0,
    },
    "nia": {
        "email": "nia@codeher.dev",
        "username": "nia",
        "display_name": "Nia (sample account)",
        "role": "learner",
        "headline": "Front-end in progress, CSS enthusiast",
        "bio": "Sample account created by `manage.py seed` so the community feed and leaderboard are not "
        "empty on a fresh install.",
        "interests": ["css", "accessibility"],
        "learning_technologies": ["HTML", "CSS", "JavaScript"],
        "skill_level": "beginner",
        "country": "Nigeria",
        "timezone_name": "Africa/Lagos",
        "weekly_goal_minutes": 90,
    },
    "sofia": {
        "email": "sofia@codeher.dev",
        "username": "sofia",
        "display_name": "Sofia (sample account)",
        "role": "learner",
        "headline": "Data-curious, learning Python",
        "bio": "Sample account created by `manage.py seed`. Fictional demonstration profile.",
        "interests": ["python", "data"],
        "learning_technologies": ["Python", "MySQL"],
        "skill_level": "intermediate",
        "country": "Brazil",
        "timezone_name": "America/Sao_Paulo",
        "weekly_goal_minutes": 150,
    },
    "omid": {
        "email": "omid@codeher.dev",
        "username": "omid",
        "display_name": "Omid (sample account)",
        "role": "learner",
        "headline": "Self-taught, chasing the security path",
        "bio": "Sample account created by `manage.py seed`. Fictional demonstration profile.",
        "interests": ["security", "networking"],
        "learning_technologies": ["Python", "Git"],
        "skill_level": "intermediate",
        "country": "Germany",
        "timezone_name": "Europe/Berlin",
        "weekly_goal_minutes": 60,
    },
    "mei": {
        "email": "mei@codeher.dev",
        "username": "mei",
        "display_name": "Mei (sample mentor)",
        "role": "mentor",
        "headline": "Security engineer · defensive web application testing",
        "bio": "Sample mentor account created by `manage.py seed`. Fictional demonstration profile.",
        "interests": ["security", "devops"],
        "learning_technologies": ["Python", "Docker"],
        "skill_level": "advanced",
        "country": "Singapore",
        "timezone_name": "Asia/Singapore",
        "weekly_goal_minutes": 30,
    },
}

MENTORS = {
    "grace": {
        "expertise": ["Django", "Python", "API design", "Interview preparation", "Career switching"],
        "availability_note": "Two slots on Tuesday evenings and one Saturday morning (UTC).",
        "preferred_slots": ["Tue 19:00 UTC", "Sat 10:00 UTC"],
        "capacity": 4,
        "years_experience": 12,
        "current_role": "Senior Backend Engineer",
        "languages": ["English"],
        "bio": "Sample mentor profile. I help people move from tutorials to shipping real systems: code "
        "review, architecture conversations, and practice interviews. Sessions are 45 minutes and I "
        "always send notes afterwards so nothing is lost.",
    },
    "mei": {
        "expertise": ["Web application security", "OWASP Top 10", "Secure coding", "Threat modelling"],
        "availability_note": "Weekday afternoons (SGT).",
        "preferred_slots": ["Wed 15:00 SGT"],
        "capacity": 2,
        "years_experience": 7,
        "current_role": "Security Engineer",
        "languages": ["English", "Chinese"],
        "bio": "Sample mentor profile. Defensive security only: I review designs and code with you and "
        "teach how to read advisories without panic.",
    },
}

POSTS = [
    {
        "author": "nia",
        "type": "question",
        "title": "When should I use CSS grid versus flexbox?",
        "body": "I keep reaching for flexbox for everything, even card galleries, and then I end up with "
        "nested wrappers. Is the rule of thumb really 'grid for two dimensions, flex for one'? "
        "A concrete example would help more than the theory.",
        "tags": ["css", "layout"],
        "course_category": "web",
        "comments": [
            {
                "author": "grace",
                "body": "The one-or-two-dimension rule is a decent start, but the sharper question is: do "
                "you want the content to decide the size, or the container? Flexbox is content-first, so "
                "items grow and shrink around what they hold. Grid is container-first, so you declare "
                "tracks and place things inside them. A card gallery with an unknown count of cards wants "
                "grid with repeat(auto-fill, minmax(240px, 1fr)). A toolbar wants flex.",
            },
            {
                "author": "ada",
                "body": "This clicked for me too. I switched my dashboard gallery to grid and deleted three "
                "wrapper divs.",
            },
        ],
    },
    {
        "author": "ada",
        "type": "experience",
        "title": "Six months from nursing to my first React component. Some honesty.",
        "body": "I want to post the unglamorous version because the highlight reels almost made me quit. "
        "For the first two months I understood nothing. I kept a paper notebook of terms, and every time "
        "I got stuck for more than twenty minutes I wrote the question down instead of solving it, then "
        "came back the next day. Almost all of them made sense on the second pass. The thing that finally "
        "made state click was building a to-do list by hand, badly, three times. If you are in month two "
        "and convinced you are not technical enough: you are just early.",
        "tags": ["careers", "learning", "react"],
        "comments": [
            {"author": "sofia", "body": "The twenty-minute rule changed my week. Stealing it."},
            {"author": "grace", "body": "This is the most useful post on the platform this month. Writing "
            "the question down is genuinely a debugging skill, not a shortcut."},
        ],
    },
    {
        "author": "omid",
        "type": "question",
        "title": "How do I actually read a CVE without a security background?",
        "body": "I can follow the security path lessons, but real advisories still read like a foreign "
        "language. What do you look at first when a new CVE lands — the description, the CVSS vector, or "
        "the affected versions?",
        "tags": ["security", "learning"],
        "comments": [
            {"author": "mei", "body": "Versions first, always. If your deployed version is not in the "
            "affected range, the rest is context rather than an incident. Only then read the description "
            "to see whether the vulnerable code path is one you actually call."},
        ],
    },
    {
        "author": "sofia",
        "type": "discussion",
        "title": "Are SQL joins underrated for analytics work?",
        "body": "Every tutorial jumps to a dataframe library, but half my day is still three tables and a "
        "join. I want to know whether I am missing something by staying in SQL.",
        "tags": ["sql", "data"],
        "comments": [
            {"author": "grace", "body": "You are not missing anything. SQL runs next to the data, which "
            "means the database planner can use indexes. Pulling a million rows into a dataframe to do "
            "what one GROUP BY does is a self-inflicted outage."},
        ],
    },
    {
        "author": "nia",
        "type": "showcase",
        "title": "My accessibility-audit site, built from the HTML and CSS path",
        "body": "It is small and the animations are terrible, but it works: you paste a URL list and it "
        "shows which pages are missing alt text or have low-contrast body copy. Built with plain JS and no "
        "framework because I wanted to understand what the framework was doing for me.",
        "tags": ["accessibility", "javascript", "project"],
        "comments": [
            {"author": "ada", "body": "No framework on purpose is such a good learning decision. Contrast "
            "checking is harder than it looks."},
        ],
    },
    {
        "author": "grace",
        "type": "discussion",
        "title": "What I look for in a junior portfolio (from the hiring side)",
        "body": "I have reviewed a lot of portfolios and the pattern is clear: one finished project with a "
        "README explaining the trade-offs beats six half-built apps. I want to see a decision you made and "
        "why. Bonus points if the deployed link actually loads and there is a section about what you would "
        "do differently with more time.",
        "tags": ["careers", "portfolio", "hiring"],
        "comments": [
            {"author": "omid", "body": "'What I would do differently' is the section nobody writes and "
            "every reviewer wants."},
            {"author": "nia", "body": "Saving this before I rewrite mine."},
        ],
    },
    {
        "author": "mei",
        "type": "question",
        "title": "How should a beginner store secrets in a small project?",
        "body": "I see people commit a .env and people insist on a secret manager. For a hobby project on "
        "GitHub, what is the honest minimum?",
        "tags": ["security", "devops"],
        "comments": [
            {"author": "grace", "body": "Minimum: .env in .gitignore, .env.example committed with the key "
            "names and no values, and a pre-commit hook that scans for tokens so a mistake never reaches "
            "the remote. A secret manager is the next step once more than one person deploys."},
        ],
    },
    {
        "author": "ada",
        "type": "question",
        "title": "git merge versus git rebase for a branch with three commits",
        "body": "My team history gets messy with merge commits, but rebase scares me. Is there a safe rule "
        "for when each is fine?",
        "tags": ["git"],
        "comments": [
            {"author": "mei", "body": "One rule: never rewrite history that anyone else has pulled. Rebase "
            "your own unpushed or personal branch; merge anything shared. That single line removes most of "
            "the danger."},
        ],
    },
]

PROJECTS = [
    {
        "author": "nia",
        "title": "Contrast Keeper",
        "description": "Paste a list of page URLs and get back which ones fail WCAG AA contrast on body "
        "copy, plus a suggested foreground colour that passes. Written in plain JavaScript with no build "
        "step, because I wanted to understand exactly what my code did.",
        "technologies": ["JavaScript", "HTML", "CSS"],
        "repo_url": "https://github.com/codeher-samples/contrast-keeper",
        "sample": True,
        "likes": 14,
        "views": 96,
    },
    {
        "author": "ada",
        "title": "Shift Planner",
        "description": "A small Django app that lets a nursing unit swap shifts and keeps an audit trail of "
        "who agreed to what. Models for staff, shifts and swap requests; the swap logic is a state machine, "
        "which was the part I actually learned from.",
        "technologies": ["Python", "Django", "MySQL"],
        "repo_url": "https://github.com/codeher-samples/shift-planner",
        "sample": True,
        "likes": 22,
        "views": 148,
    },
    {
        "author": "sofia",
        "title": "Query Notebook",
        "description": "A browser-based SQL playground that runs your queries against a tiny in-browser "
        "dataset and explains which part of your query the engine evaluated first. Built while working "
        "through the MySQL path.",
        "technologies": ["JavaScript", "SQL"],
        "live_url": "https://codeher-samples.github.io/query-notebook/",
        "sample": True,
        "likes": 31,
        "views": 240,
    },
    {
        "author": "omid",
        "title": "Advisory Digest",
        "description": "Pulls public security advisories, filters them to the packages in your lockfile, and "
        "renders the ones that actually apply to your installed versions. Defensive tooling only, no exploit "
        "content.",
        "technologies": ["Python", "REST API"],
        "repo_url": "https://github.com/codeher-samples/advisory-digest",
        "sample": True,
        "likes": 18,
        "views": 132,
    },
    {
        "author": "grace",
        "title": "Django DRF Boilerplate",
        "description": "The starting point I give every mentee: custom user model, JWT with token rotation, "
        "pagination, error shape, health check and a CI config that runs the tests. Read it top to bottom "
        "before your first interview.",
        "technologies": ["Python", "Django", "MySQL"],
        "repo_url": "https://github.com/codeher-samples/drf-boilerplate",
        "sample": True,
        "likes": 47,
        "views": 380,
    },
]

# starts_in_days is relative to the moment you run the command, so the landing page
# always has genuine upcoming events instead of stale dates.
EVENTS = [
    {
        "title": "Study group: CSS layout clinic",
        "kind": "study_group",
        "description": "Bring the layout you cannot fix. We work through them live, screen shared.",
        "starts_in_days": 2,
        "duration_minutes": 60,
    },
    {
        "title": "Workshop: your first Django model",
        "kind": "workshop",
        "description": "From an empty app to a migrated table, with the reasoning behind every file.",
        "starts_in_days": 4,
        "duration_minutes": 90,
    },
    {
        "title": "Office hours with Grace",
        "kind": "office_hours",
        "description": "Open door for anything: code review requests, career questions, stuck logic.",
        "starts_in_days": 6,
        "duration_minutes": 120,
    },
    {
        "title": "Webinar: reading a job description as a junior",
        "kind": "webinar",
        "description": "How to tell requirements from wishes, and what to write in the cover note.",
        "starts_in_days": 9,
        "duration_minutes": 45,
    },
    {
        "title": "Hackathon: build something in a weekend",
        "kind": "hackathon",
        "description": "Teams of two to four, one finished project each, judged on the write-up.",
        "starts_in_days": 14,
        "duration_minutes": 2880,
    },
    {
        "title": "Study group: SQL joins, together",
        "kind": "study_group",
        "description": "Work through the join exercises in the MySQL path with other learners.",
        "starts_in_days": 20,
        "duration_minutes": 60,
    },
]
