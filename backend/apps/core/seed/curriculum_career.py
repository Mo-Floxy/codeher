"""Clearly labelled demonstration content for manage.py seed."""

GIT_GITHUB = {
    "title": "Git and GitHub",
    "slug": "git-and-github",
    "level": "beginner",
    "color": "#f97316",
    "icon": "GitBranch",
    "description": "Track your changes, undo safely and collaborate. You will learn Git's three areas, then "
    "branch, merge and open pull requests with the GitHub workflow used by real teams.",
    "courses": [
        {
            "title": "Git Essentials",
            "subtitle": "Version control on your own machine — commit, branch and merge.",
            "level": "beginner",
            "category": "career",
            "duration_hours": 7,
            "objectives": [
                "Explain the working directory, staging area and repository",
                "Make commits and branch with confidence",
                "Merge a feature branch back into main",
            ],
            "requirements": ["A terminal and Git installed (git --version to check). No prior Git needed."],
            "modules": [
                {
                    "title": "Your first repository",
                    "summary": "Where changes live before they become history.",
                    "lessons": [
                        {
                            "title": "The three areas",
                            "kind": "text",
                            "summary": "Working directory, staging area, repository — the mental model that makes Git click.",
                            "paragraphs": [
                                "Git keeps your files in three places. The working directory is what you are "
                                "editing right now. The staging area is the set of changes you have chosen to "
                                "include in the next snapshot. The repository is the saved history of those "
                                "snapshots, called commits.",
                                "You edit freely, then git add picks which edits to stage, and git commit records "
                                "the staged snapshot. This two-step is the superpower: you decide exactly what "
                                "goes into each commit, so your history tells a clear story.",
                            ],
                            "bullets": [
                                "git status always shows which area your changes are in",
                                "A commit message should say why, not just what changed",
                                "Nothing is saved to history until you commit",
                            ],
                            "estimated_minutes": 11,
                        },
                        {
                            "title": "Init, stage and commit",
                            "kind": "code",
                            "summary": "The first five commands you will use constantly.",
                            "paragraphs": [
                                "git init turns a folder into a repository. Then you stage a file, commit it, and "
                                "inspect the result. Run these one at a time and watch git status between steps.",
                            ],
                            "code": {
                                "language": "bash",
                                "caption": "From empty folder to first commit",
                                "code": """mkdir my-project
cd my-project
git init
git status
echo "Hello" > notes.txt
git add notes.txt
git commit -m "Add the first note"
git log --oneline""",
                            },
                            "note": "git commit -m takes the message inline. Without -m, Git opens your editor instead.",
                            "estimated_minutes": 12,
                        },
                        {
                            "title": "Check your understanding",
                            "kind": "quiz",
                            "summary": "Four questions on Git's three areas.",
                            "paragraphs": ["Four questions to check the mental model before we branch."],
                            "questions": [
                                {
                                    "prompt": "Which command chooses changes to include in the next commit?",
                                    "choices": ["git commit", "git add", "git status", "git init"],
                                    "correct": 1,
                                    "explanation": "git add moves edits from the working directory into the staging area.",
                                },
                                {
                                    "prompt": "When does a change become part of Git's history?",
                                    "choices": ["When you edit the file", "When you git add it", "When you git commit it", "Immediately"],
                                    "correct": 2,
                                    "explanation": "Only a commit writes a permanent snapshot into the repository.",
                                },
                                {
                                    "prompt": "Which command shows which of the three areas your changes are sitting in?",
                                    "choices": ["git status", "git log", "git init", "git clone"],
                                    "correct": 0,
                                    "explanation": "git status reports which area each change is in, so you can see the difference between edited and staged.",
                                },
                                {
                                    "prompt": "What does git commit do if you leave out -m?",
                                    "choices": [
                                        "It commits with an empty message",
                                        "It refuses to commit anything",
                                        "It opens your editor so you can write the message",
                                        "It commits every file in the working directory",
                                    ],
                                    "correct": 2,
                                    "explanation": "The -m flag supplies the message inline; without it Git waits for you to write one in an editor.",
                                },
                            ],
                            "estimated_minutes": 5,
                        },
                    ],
                },
                {
                    "title": "Branches and merging",
                    "summary": "Try things in parallel without breaking the main line.",
                    "lessons": [
                        {
                            "title": "Why branches",
                            "kind": "text",
                            "summary": "A branch is just a movable pointer to a commit.",
                            "paragraphs": [
                                "The default branch is usually called main and represents the stable line of "
                                "work. A branch lets you develop a feature or fix in isolation, so an experiment "
                                "cannot break the good version while you build it.",
                                "git switch creates or moves you between branches. When the work is done and "
                                "reviewed, git merge folds the branch's commits back into main. If nothing else "
                                "changed, Git does a fast-forward merge automatically.",
                            ],
                            "bullets": [
                                "Name branches by intent: feature/dark-mode, fix/login-crash",
                                "Merge commits record that two lines of history were combined",
                                "git log --graph makes the branching visible",
                            ],
                            "estimated_minutes": 11,
                        },
                        {
                            "title": "Branch, work and merge",
                            "kind": "code",
                            "summary": "The full arc of a small feature.",
                            "paragraphs": [
                                "Start a branch off main, make a commit, switch back to main, then merge. The "
                                "last command shows a compact, readable history.",
                            ],
                            "code": {
                                "language": "bash",
                                "caption": "A complete feature cycle",
                                "code": """git switch -c feature/dark-mode
git add .
git commit -m "Add a dark theme toggle"
git switch main
git merge feature/dark-mode
git log --oneline --graph --decorate -5""",
                            },
                            "note": "git switch -c name means 'create and switch to' a new branch. The older git checkout -c form does the same thing.",
                            "estimated_minutes": 12,
                        },
                        {
                            "title": "Check your understanding",
                            "kind": "quiz",
                            "summary": "Four questions on branches and merging.",
                            "paragraphs": ["Four questions on working in parallel."],
                            "questions": [
                                {
                                    "prompt": "What does git switch -c feature/x do?",
                                    "choices": [
                                        "Deletes branch feature/x",
                                        "Creates feature/x and moves you onto it",
                                        "Merges feature/x into main",
                                        "Renames the current branch",
                                    ],
                                    "correct": 1,
                                    "explanation": "The -c flag creates the branch and switches to it in one step.",
                                },
                                {
                                    "prompt": "Why develop a risky change on its own branch?",
                                    "choices": [
                                        "It is faster than editing",
                                        "So it cannot affect the stable main line until it is ready",
                                        "Branches store less data",
                                        "It avoids ever committing",
                                    ],
                                    "correct": 1,
                                    "explanation": "Isolation lets you experiment freely and merge only when it is good.",
                                },
                                {
                                    "prompt": "In Git's model, what is a branch?",
                                    "choices": [
                                        "A movable pointer to a commit",
                                        "A copy of every file in the project",
                                        "A separate folder on disk",
                                        "A remote repository",
                                    ],
                                    "correct": 0,
                                    "explanation": "Git keeps the commits and simply points at one of them, which is why creating a branch is instant.",
                                },
                                {
                                    "prompt": "When does Git do a fast-forward merge automatically?",
                                    "choices": [
                                        "When the two branches conflict",
                                        "When nothing else changed on the branch being merged into",
                                        "When you delete the feature branch first",
                                        "Only if you ask for it by name",
                                    ],
                                    "correct": 1,
                                    "explanation": "If main did not move while you worked, Git can advance the pointer instead of recording a merge commit.",
                                },
                            ],
                            "estimated_minutes": 5,
                        },
                    ],
                },
            ],
        },
        {
            "title": "GitHub and Teamwork",
            "subtitle": "Sync with a remote and contribute through pull requests.",
            "level": "intermediate",
            "category": "career",
            "duration_hours": 8,
            "objectives": [
                "Clone, push and pull between your machine and GitHub",
                "Ignore files that should never be committed",
                "Contribute with a fork, a branch and a pull request, and resolve a conflict",
            ],
            "requirements": ["'Git Essentials' and a free GitHub account."],
            "modules": [
                {
                    "title": "Remotes and .gitignore",
                    "summary": "Your local repository and a copy on GitHub, kept in step.",
                    "lessons": [
                        {
                            "title": "Push, pull and what to ignore",
                            "kind": "text",
                            "summary": "A remote is simply another copy of your repository.",
                            "paragraphs": [
                                "GitHub hosts your repository at a URL called a remote, conventionally named "
                                "origin. git clone makes a local copy of it. git push uploads your commits, and "
                                "git pull fetches other people's commits and merges them, so both copies converge.",
                                "A .gitignore file lists patterns Git should not track — virtual environments, "
                                "caches and build output. Ignoring them keeps your repository light and avoids "
                                "committing machine-specific noise. Never commit secrets: use .gitignore for the "
                                "files that hold them.",
                            ],
                            "bullets": [
                                "git push -u origin main sets the upstream so later pushes need no arguments",
                                "Adding to .gitignore stops tracking, but already-tracked files need git rm --cached",
                                "The .env, .venv/ and __pycache__/ patterns are common ones to start with",
                            ],
                            "estimated_minutes": 11,
                        },
                        {
                            "title": "Clone, ignore and push",
                            "kind": "code",
                            "summary": "Bring a repo down, tidy it, and send work back up.",
                            "paragraphs": [
                                "Clone once, then every cycle is the same: make a commit, push it up, and pull "
                                "before you start so you are not surprised by changes others pushed.",
                            ],
                            "code": {
                                "language": "bash",
                                "caption": "Talking to origin",
                                "code": """git clone https://github.com/you/codeher-notes.git
cd codeher-notes
echo ".venv/" >> .gitignore
echo "__pycache__/" >> .gitignore
git add .
git commit -m "Ignore the virtual environment and caches"
git push -u origin main
git pull origin main""",
                            },
                            "estimated_minutes": 12,
                        },
                        {
                            "title": "Check your understanding",
                            "kind": "quiz",
                            "summary": "Four questions on remotes and ignoring files.",
                            "paragraphs": ["Four questions about syncing and tidiness."],
                            "questions": [
                                {
                                    "prompt": "What is 'origin'?",
                                    "choices": [
                                        "The first commit",
                                        "The default name for the main remote repository",
                                        "Your local working directory",
                                        "The main branch",
                                    ],
                                    "correct": 1,
                                    "explanation": "origin is the conventional name for the remote copy, usually on GitHub.",
                                },
                                {
                                    "prompt": "Why add a file to .gitignore?",
                                    "choices": [
                                        "To delete it from disk",
                                        "So Git stops tracking that kind of file",
                                        "To encrypt it",
                                        "To share it with the team",
                                    ],
                                    "correct": 1,
                                    "explanation": "It keeps generated, large or secret files out of the repository.",
                                },
                                {
                                    "prompt": "What does git pull do?",
                                    "choices": [
                                        "Uploads your commits to the remote",
                                        "Fetches other people's commits and merges them",
                                        "Deletes the local copy of the repository",
                                        "Creates a new branch on GitHub",
                                    ],
                                    "correct": 1,
                                    "explanation": "Push sends your commits up; pull brings other commits down and merges them, so both copies converge.",
                                },
                                {
                                    "prompt": "Why run git push -u origin main the first time?",
                                    "choices": [
                                        "It forces the push past any conflict",
                                        "It uploads every branch at the same time",
                                        "It records the upstream, so later pushes need no arguments",
                                        "It creates the main branch on your machine",
                                    ],
                                    "correct": 2,
                                    "explanation": "The -u flag links your local main to origin main, so a plain git push is enough from then on.",
                                },
                            ],
                            "estimated_minutes": 5,
                        },
                    ],
                },
                {
                    "title": "Forks, pull requests and conflicts",
                    "summary": "How teams review work before it lands.",
                    "lessons": [
                        {
                            "title": "The fork and PR workflow",
                            "kind": "text",
                            "summary": "Contribute to someone else's project safely.",
                            "paragraphs": [
                                "When you cannot push to a repository directly, you fork it — GitHub makes a copy "
                                "under your account — then clone that fork and work on a branch. Pushing the "
                                "branch back to your fork lets you open a pull request against the original. A "
                                "pull request is a reviewable proposal: teammates comment and request changes "
                                "before it is merged.",
                                "Conflicts happen when two branches change the same lines. Git inserts markers "
                                "into the file and leaves the decision to you: keep yours, keep theirs, or "
                                "combine them, delete the markers, then add and commit the resolution.",
                            ],
                            "bullets": [
                                "Fork -> clone your fork -> branch -> push -> open a pull request",
                                "git pull upstream main keeps your fork current with the original",
                                "Conflict markers are <<<<<<< ======= and >>>>>>> — they are a to-do, not an error",
                            ],
                            "estimated_minutes": 12,
                        },
                        {
                            "title": "A branch, a PR and a conflict",
                            "kind": "code",
                            "summary": "From a fix to a merged pull request.",
                            "paragraphs": [
                                "Commit a small fix on its own branch, push it, and open the pull request. The "
                                "comment lines show what a conflict looks like and how you finish resolving one.",
                            ],
                            "code": {
                                "language": "bash",
                                "caption": "Contributing and resolving",
                                "code": """git checkout -b fix/readme-typo
git commit -am "Fix a typo in the README"
git push -u origin fix/readme-typo
# Open the pull request on GitHub and request review.
# On a conflict Git writes markers into the file:
#   <<<<<<< HEAD        (your change)
#   =======             (the incoming change)
#   >>>>>>> fix/branch
# Edit to keep what you want, delete the markers, then:
git add README.md
git commit -m "Resolve merge conflict in README"
git log --oneline --graph""",
                            },
                            "note": "The lines starting with # are comments to read, not commands to run — Git never executes them.",
                            "estimated_minutes": 13,
                        },
                        {
                            "title": "Check your understanding",
                            "kind": "quiz",
                            "summary": "Four questions on forks, PRs and conflicts.",
                            "paragraphs": ["Four questions to close out the collaboration path."],
                            "questions": [
                                {
                                    "prompt": "What is a pull request?",
                                    "choices": [
                                        "A command that downloads files",
                                        "A proposed set of changes opened for review before merging",
                                        "A type of branch",
                                        "A way to delete a repository",
                                    ],
                                    "correct": 1,
                                    "explanation": "It invites review and discussion before your changes join the main line.",
                                },
                                {
                                    "prompt": "What do you do when Git reports a merge conflict?",
                                    "choices": [
                                        "Re-clone the repository",
                                        "Delete both versions",
                                        "Edit the file to resolve it, then add and commit",
                                        "Nothing — Git always fixes it itself",
                                    ],
                                    "correct": 2,
                                    "explanation": "Conflicts are handed to you: decide the final content, remove the markers, commit.",
                                },
                                {
                                    "prompt": "Why fork a repository instead of cloning the original?",
                                    "choices": [
                                        "Because a fork merges itself into the original",
                                        "Because you cannot push to the original, so you push to your own copy",
                                        "Because forks are smaller and quicker to clone",
                                        "Because only forks allow branches",
                                    ],
                                    "correct": 1,
                                    "explanation": "GitHub makes the copy under your account, you push your branch there, and then open a pull request against the original.",
                                },
                                {
                                    "prompt": "What is git pull upstream main for?",
                                    "choices": [
                                        "It sends your commits to the original project",
                                        "It keeps your fork current with the original repository",
                                        "It closes your open pull requests",
                                        "It deletes branches that were merged",
                                    ],
                                    "correct": 1,
                                    "explanation": "Pulling from the upstream source brings in its new commits so your fork does not fall behind.",
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

FULL_STACK = {
    "title": "Full-Stack Foundations",
    "slug": "full-stack-foundations",
    "level": "intermediate",
    "color": "#8b5cf6",
    "icon": "Layers",
    "description": "See the whole system at once. You will follow a click all the way to the database, then "
    "add authentication, understand CORS, and ship with environment variables — the connective tissue "
    "between frontend and backend.",
    "courses": [
        {
            "title": "From Click to Database",
            "subtitle": "How a request travels and how a REST API answers it.",
            "level": "intermediate",
            "category": "career",
            "duration_hours": 9,
            "objectives": [
                "Trace a request from the browser through the API to the database",
                "Call an API with fetch and handle the JSON response",
                "Read HTTP verbs and status codes correctly",
            ],
            "requirements": ["Comfortable with JavaScript basics and a little Django, or the other two paths."],
            "modules": [
                {
                    "title": "The request journey",
                    "summary": "The layers a full-stack app is made of.",
                    "lessons": [
                        {
                            "title": "How the pieces fit",
                            "kind": "text",
                            "summary": "Client, network, server, database — one round trip.",
                            "paragraphs": [
                                "A user action in the browser creates a request. It crosses the network to a "
                                "server, which runs application code and often queries a database. The result "
                                "travels back as a response, and the browser renders it. 'Full-stack' means you "
                                "can reason about every one of those hops.",
                                "The frontend (HTML, CSS, JavaScript) handles what people see and do. The backend "
                                "(a framework like Django) handles rules and data. The API is the agreed "
                                "contract between them: URLs, verbs, JSON shapes and status codes that both sides "
                                "trust.",
                            ],
                            "bullets": [
                                "The browser is the client; the program that answers is the server",
                                "Stateless HTTP means each request must carry the information it needs",
                                "The API contract is what lets the two teams work independently",
                            ],
                            "estimated_minutes": 11,
                        },
                        {
                            "title": "Calling an API with fetch",
                            "kind": "code",
                            "summary": "One async function that reads JSON and reports failure.",
                            "paragraphs": [
                                "fetch starts a request and hands back a response promise. Note that fetch only "
                                "rejects on network failure — a 404 or 500 still resolves — so you must check "
                                "response.ok yourself before parsing the body.",
                            ],
                            "code": {
                                "language": "javascript",
                                "caption": "A tiny API client",
                                "code": """async function loadCourse(slug) {
  const response = await fetch(`/api/courses/${slug}/`);
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }
  return response.json();
}

loadCourse("python-programming")
  .then((course) => console.log(course.title))
  .catch((error) => console.error(error.message));""",
                            },
                            "note": "response.json() also returns a promise, so it must be awaited too — forgetting that is the most common fetch mistake.",
                            "estimated_minutes": 13,
                        },
                        {
                            "title": "Check your understanding",
                            "kind": "quiz",
                            "summary": "Four questions on the request journey.",
                            "paragraphs": ["Four questions on how the layers talk."],
                            "questions": [
                                {
                                    "prompt": "What is an API in a full-stack app?",
                                    "choices": [
                                        "The database engine",
                                        "The agreed contract of URLs, verbs and JSON between frontend and backend",
                                        "A CSS framework",
                                        "The browser cache",
                                    ],
                                    "correct": 1,
                                    "explanation": "It is the shared set of rules both sides rely on to communicate.",
                                },
                                {
                                    "prompt": "A request returns HTTP 404. Does fetch reject the promise?",
                                    "choices": ["Yes, any non-200 rejects", "No — it resolves; you must check response.ok", "Only on a timeout", "Only for 500 errors"],
                                    "correct": 1,
                                    "explanation": "fetch rejects only on network failure; status errors must be checked manually.",
                                },
                                {
                                    "prompt": "What does it mean that HTTP is stateless?",
                                    "choices": [
                                        "The server keeps no data in a database",
                                        "Each request must carry the information it needs",
                                        "Requests are not allowed to send a body",
                                        "Every visit opens a new browser tab",
                                    ],
                                    "correct": 1,
                                    "explanation": "The server remembers nothing between requests, so context and credentials travel with each one.",
                                },
                                {
                                    "prompt": "Why must you also await response.json()?",
                                    "choices": [
                                        "Because reading the body is itself an asynchronous step",
                                        "Because fetch hands back a string, not an object",
                                        "Because JSON is larger than HTML",
                                        "Because the server sends its headers later",
                                    ],
                                    "correct": 0,
                                    "explanation": "response.json() returns a promise too, so skipping that await leaves you holding an unfinished body.",
                                },
                            ],
                            "estimated_minutes": 5,
                        },
                    ],
                },
                {
                    "title": "REST, status codes and JSON",
                    "summary": "The vocabulary every API speaks.",
                    "lessons": [
                        {
                            "title": "Verbs and codes",
                            "kind": "text",
                            "summary": "One verb per action, one status per result.",
                            "paragraphs": [
                                "REST maps actions onto verbs: GET reads (never changes anything), POST creates, "
                                "PUT replaces, PATCH updates part of a resource, DELETE removes. The response "
                                "carries a status code so the client knows what happened without guessing.",
                                "Group the codes by their first digit: 2xx success, 3xx redirects, 4xx client "
                                "error (400 bad request, 401 not authenticated, 403 forbidden, 404 not found), "
                                "5xx server error (500). Getting these right is a large part of building an API "
                                "people can trust.",
                            ],
                            "bullets": [
                                "200 OK for a successful read, 201 Created after a successful POST",
                                "204 No Content for a success with nothing to return, such as a delete",
                                "JSON is the body format: an object or array of simple values",
                            ],
                            "estimated_minutes": 12,
                        },
                        {
                            "title": "Returning the right status",
                            "kind": "code",
                            "summary": "A create action that answers 400 or 201 as appropriate.",
                            "paragraphs": [
                                "The view serializes the incoming data; if validation fails it responds with the "
                                "field errors and a 400, and on success it saves and returns 201.",
                            ],
                            "code": {
                                "language": "django",
                                "caption": "A REST create action",
                                "code": """from rest_framework import viewsets, status
from rest_framework.response import Response

class NoteViewSet(viewsets.ModelViewSet):
    queryset = Note.objects.all()
    serializer_class = NoteSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)""",
                            },
                            "note": "The model and serializer imports are left out of this snippet to keep the flow clear.",
                            "estimated_minutes": 13,
                        },
                        {
                            "title": "Check your understanding",
                            "kind": "quiz",
                            "summary": "Four questions on verbs and status codes.",
                            "paragraphs": ["Four questions on the shared API vocabulary."],
                            "questions": [
                                {
                                    "prompt": "Which status best fits a newly created resource?",
                                    "choices": ["200 OK", "201 Created", "400 Bad Request", "301 Moved"],
                                    "correct": 1,
                                    "explanation": "201 signals that the POST created something new.",
                                },
                                {
                                    "prompt": "The difference between 401 and 403 is:",
                                    "choices": [
                                        "None, they are interchangeable",
                                        "401 means not authenticated; 403 means authenticated but not permitted",
                                        "403 is success; 401 is failure",
                                        "401 is a client error; 403 is a server error",
                                    ],
                                    "correct": 1,
                                    "explanation": "One is about who you are, the other about what you are allowed to do.",
                                },
                                {
                                    "prompt": "Which status fits a successful DELETE that returns nothing?",
                                    "choices": ["200 OK", "201 Created", "204 No Content", "301 Moved"],
                                    "correct": 2,
                                    "explanation": "204 signals that the action worked and that the empty body is deliberate.",
                                },
                                {
                                    "prompt": "What does a status code in the 5xx range tell the client?",
                                    "choices": [
                                        "The request was redirected",
                                        "The server failed",
                                        "The client sent bad data",
                                        "A new resource now exists",
                                    ],
                                    "correct": 1,
                                    "explanation": "Codes group by first digit: 2xx success, 3xx redirects, 4xx client error and 5xx server error.",
                                },
                            ],
                            "estimated_minutes": 5,
                        },
                    ],
                },
            ],
        },
        {
            "title": "Auth, CORS and Shipping",
            "subtitle": "Protect the API, cross the browser's rules, and deploy safely.",
            "level": "intermediate",
            "category": "career",
            "duration_hours": 9,
            "objectives": [
                "Send a token with requests and understand what it proves",
                "Explain same-origin policy and why CORS errors appear",
                "Configure an app through environment variables and follow a deploy checklist",
            ],
            "requirements": ["'From Click to Database' or comfortable calling an API from the browser."],
            "modules": [
                {
                    "title": "Authentication and CORS",
                    "summary": "Proving who you are, and the browser's permission checks.",
                    "lessons": [
                        {
                            "title": "Tokens and same-origin",
                            "kind": "text",
                            "summary": "How the browser lets (or blocks) a request, and how identity travels.",
                            "paragraphs": [
                                "After you sign in, the server issues a token — often a JSON Web Token (JWT). The "
                                "browser sends it back on later requests, usually in an Authorization header as "
                                "Bearer <token>, so the server knows who is asking without a password each time. A "
                                "JWT is signed, not secret: anyone can read it, so never put confidential data inside, "
                                "and keep access tokens short-lived.",
                                "CORS is a browser rule: a page can only read responses from another origin unless "
                                "that server opts in with headers like Access-Control-Allow-Origin. Preflight "
                                "requests (an automatic OPTIONS call) happen for requests the browser considers "
                                "unsafe. CORS only governs the browser; server-to-server calls are not restricted.",
                            ],
                            "bullets": [
                                "Authorization: Bearer <token> is the usual header for a JWT",
                                "A CORS error means the server did not allow that origin — it is not your token failing",
                                "Tokens in localStorage are convenient but readable by scripts; httpOnly cookies are safer",
                            ],
                            "estimated_minutes": 13,
                        },
                        {
                            "title": "Sending the token",
                            "kind": "code",
                            "summary": "Attach the Authorization header to a write request.",
                            "paragraphs": [
                                "The browser reads the saved token and adds it to the headers of the request that "
                                "enrols you in a course. A 201 means it worked; anything else, you handle it.",
                            ],
                            "code": {
                                "language": "javascript",
                                "caption": "An authenticated POST",
                                "code": """const accessToken = localStorage.getItem("access_token");

fetch("/api/enrollments/", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${accessToken}`,
  },
  body: JSON.stringify({ course_id: 42 }),
})
  .then((response) => (response.status === 201 ? console.log("Enrolled!") : console.warn("Try again")))
  .catch((error) => console.error(error));""",
                            },
                            "note": "Read the CORS text before trusting localStorage for tokens; the safe default for new projects is an httpOnly cookie set by the server.",
                            "estimated_minutes": 12,
                        },
                        {
                            "title": "Check your understanding",
                            "kind": "quiz",
                            "summary": "Four questions on auth and CORS.",
                            "paragraphs": ["Four questions on identity and the browser's gate."],
                            "questions": [
                                {
                                    "prompt": "A CORS error in the console usually means:",
                                    "choices": [
                                        "Your token has expired",
                                        "The server did not allow requests from this origin",
                                        "The database is down",
                                        "Your JavaScript has a typo",
                                    ],
                                    "correct": 1,
                                    "explanation": "CORS is about the origin being allowed to read the response, not about authentication.",
                                },
                                {
                                    "prompt": "Why should a JWT never contain confidential data?",
                                    "choices": [
                                        "It is encrypted but slow",
                                        "It is only signed, so its contents are readable to anyone",
                                        "Tokens cannot hold text",
                                        "It expires instantly",
                                    ],
                                    "correct": 1,
                                    "explanation": "The signature proves integrity, not secrecy — decode any JWT to read its payload.",
                                },
                                {
                                    "prompt": "Where does the browser usually put a JWT on a request?",
                                    "choices": [
                                        "In the URL query string",
                                        "In an Authorization header as Bearer <token>",
                                        "In the Content-Type header",
                                        "As a form field named token",
                                    ],
                                    "correct": 1,
                                    "explanation": "Sending the token in the Authorization header tells the server who is asking, with no password each time.",
                                },
                                {
                                    "prompt": "Why is an httpOnly cookie a safer home for a token than localStorage?",
                                    "choices": [
                                        "Scripts running on the page cannot read it",
                                        "The browser encrypts it",
                                        "It never expires",
                                        "It never crosses the network",
                                    ],
                                    "correct": 0,
                                    "explanation": "Anything stored in localStorage is readable by page scripts, while an httpOnly cookie stays out of their reach.",
                                },
                            ],
                            "estimated_minutes": 5,
                        },
                    ],
                },
                {
                    "title": "Configuration and deployment",
                    "summary": "Environment variables and a pre-launch checklist.",
                    "lessons": [
                        {
                            "title": "Config and a deploy checklist",
                            "kind": "text",
                            "summary": "Different values per environment, no secrets in the repo.",
                            "paragraphs": [
                                "An environment variable is a value the operating system hands your program at "
                                "runtime, so the same code reads different settings on your laptop, on staging "
                                "and in production. Secrets like SECRET_KEY or a database password go here and "
                                "are never committed — a .env file holding them is added to .gitignore.",
                                "Before going live, run a checklist: turn DEBUG off, set ALLOWED_HOSTS, serve "
                                "static files, apply migrations, put the site behind HTTPS, and point the "
                                "database at a real server with backups. Most 'my app broke in production' bugs "
                                "are a setting that was only ever right on one machine.",
                            ],
                            "bullets": [
                                "Read config from the environment: os.environ['DJANGO_SECRET_KEY']",
                                "DEBUG=False and a proper ALLOWED_HOSTS in production",
                                "Never paste a real secret into an issue or a pull request",
                            ],
                            "estimated_minutes": 12,
                        },
                        {
                            "title": "Environment variables at work",
                            "kind": "code",
                            "summary": "Keep secrets out of git and prepare the app to serve.",
                            "paragraphs": [
                                "The .env stays out of the repository, the values are exported, and then two "
                                "management commands get the app ready to serve. The final curl is a smoke test.",
                            ],
                            "code": {
                                "language": "bash",
                                "caption": "Config plus a health check",
                                "code": """echo ".env" >> .gitignore

export DJANGO_SECRET_KEY="paste-your-long-random-value"
export DJANGO_DEBUG="False"
export DJANGO_ALLOWED_HOSTS="codeher.example"

python manage.py collectstatic --noinput
python manage.py migrate --noinput
curl -f https://codeher.example/health/""",
                            },
                            "note": "The -f flag makes curl exit with an error if the server returns a 4xx or 5xx, so it works as a simple pass/fail check.",
                            "estimated_minutes": 12,
                        },
                        {
                            "title": "Check your understanding",
                            "kind": "quiz",
                            "summary": "Four questions on config and deployment.",
                            "paragraphs": ["Four questions to finish the full-stack path."],
                            "questions": [
                                {
                                    "prompt": "Where should a production SECRET_KEY live?",
                                    "choices": [
                                        "Committed in settings.py",
                                        "An environment variable or secret manager, never in git",
                                        "The database as a row",
                                        "The README",
                                    ],
                                    "correct": 1,
                                    "explanation": "Anything in version control leaks to everyone with repo access.",
                                },
                                {
                                    "prompt": "Why must DEBUG be False in production?",
                                    "choices": [
                                        "It is slower",
                                        "Error pages can expose source code and configuration",
                                        "Migrations stop running",
                                        "It disables HTTPS",
                                    ],
                                    "correct": 1,
                                    "explanation": "Debug tracebacks reveal internal details that attackers can use.",
                                },
                                {
                                    "prompt": "What are environment variables good for?",
                                    "choices": [
                                        "Letting the same code read different settings on each machine",
                                        "Holding the contents of the database",
                                        "Speeding up the first request after a deploy",
                                        "Replacing the need to run migrations",
                                    ],
                                    "correct": 0,
                                    "explanation": "The operating system hands the value to the program at runtime, so laptop, staging and production can differ with no code change.",
                                },
                                {
                                    "prompt": "Why does the health check use curl -f?",
                                    "choices": [
                                        "It fetches the page twice for a better average",
                                        "It follows redirects through to HTTPS",
                                        "It exits with an error when the server returns a 4xx or 5xx",
                                        "It prints only the status line",
                                    ],
                                    "correct": 2,
                                    "explanation": "That flag turns a 4xx or 5xx into a failed command, so the request works as a simple pass-or-fail check.",
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

CYBERSECURITY = {
    "title": "Cybersecurity Basics",
    "slug": "cybersecurity-basics",
    "level": "beginner",
    "color": "#ef4444",
    "icon": "ShieldCheck",
    "description": "Think like a defender. You will learn the CIA triad, threat modeling and the OWASP Top 10, "
    "then the everyday practices that make software safe: hashing passwords, validating input, protecting "
    "secrets and using HTTPS. This path is defensive and educational only.",
    "courses": [
        {
            "title": "Security Fundamentals",
            "subtitle": "What you are protecting, from whom, and how the common risks are grouped.",
            "level": "beginner",
            "category": "career",
            "duration_hours": 7,
            "objectives": [
                "Explain confidentiality, integrity and availability",
                "Use threat modeling and least privilege to shrink the surface",
                "Recognise the categories in the OWASP Top 10 and their main fixes",
            ],
            "requirements": ["Comfortable reading code in any language. No security background assumed."],
            "modules": [
                {
                    "title": "The CIA triad and threat modeling",
                    "summary": "The three properties you protect and how to reason about risk.",
                    "lessons": [
                        {
                            "title": "What 'secure' actually means",
                            "kind": "text",
                            "summary": "Confidentiality, integrity and availability, plus the mindset of least privilege.",
                            "paragraphs": [
                                "Almost every security decision protects one of three things, known as the CIA "
                                "triad. Confidentiality means only authorised people can see data. Integrity "
                                "means data is not tampered with. Availability means the system is up when "
                                "people need it. A single breach can damage one or more of these.",
                                "Threat modeling means asking, before you build, 'who might attack this, what "
                                "would they want, and what could go wrong?'. The answer drives defense in depth "
                                "— several overlapping safeguards — and least privilege, the rule that every "
                                "user and every process gets only the access it truly needs, and nothing more.",
                            ],
                            "bullets": [
                                "Least privilege is the single habit that prevents the most damage",
                                "Defense in depth assumes one control can fail",
                                "You cannot protect what you have not identified: map your data and entry points",
                            ],
                            "estimated_minutes": 12,
                        },
                        {
                            "title": "Enforcing least privilege",
                            "kind": "code",
                            "summary": "Default-deny is safer than listing the forbidden actions.",
                            "paragraphs": [
                                "This is the core idea behind permission systems: rather than assume an action "
                                "is allowed unless it is banned, assume it is forbidden unless the role "
                                "explicitly grants it. New actions are then denied by default.",
                            ],
                            "code": {
                                "language": "python",
                                "caption": "A tiny role check",
                                "code": """ROLE_PERMISSIONS = {
    "learner": {"view_course", "post_comment"},
    "mentor": {"view_course", "post_comment", "grade_assignment"},
    "admin": {"view_course", "post_comment", "grade_assignment", "delete_user"},
}

def allowed(role, action):
    # Default-deny: allowed only if the role explicitly lists the action.
    return action in ROLE_PERMISSIONS.get(role, set())

print(allowed("learner", "grade_assignment"))  # False
print(allowed("mentor", "grade_assignment"))   # True""",
                            },
                            "note": "Unknown or missing roles fall through to an empty set, so they are denied every action.",
                            "estimated_minutes": 12,
                        },
                        {
                            "title": "Check your understanding",
                            "kind": "quiz",
                            "summary": "Four questions on the CIA triad and least privilege.",
                            "paragraphs": ["Four questions on the foundations of defence."],
                            "questions": [
                                {
                                    "prompt": "Which CIA property is broken when an outage makes the site unreachable?",
                                    "choices": ["Confidentiality", "Integrity", "Availability", "Authentication"],
                                    "correct": 2,
                                    "explanation": "Availability is about the system being up when people need it.",
                                },
                                {
                                    "prompt": "Least privilege means a user gets:",
                                    "choices": [
                                        "Admin rights so nothing is blocked",
                                        "Only the access they genuinely need, and nothing more",
                                        "All read permissions",
                                        "A shared password",
                                    ],
                                    "correct": 1,
                                    "explanation": "Limiting access limits the damage if an account is abused.",
                                },
                                {
                                    "prompt": "What does defense in depth assume?",
                                    "choices": [
                                        "That one strong control is enough",
                                        "That any single control might fail, so safeguards overlap",
                                        "That only outsiders can cause harm",
                                        "That backups make monitoring unnecessary",
                                    ],
                                    "correct": 1,
                                    "explanation": "Several overlapping safeguards mean one broken control does not expose everything that was behind it.",
                                },
                                {
                                    "prompt": "In the role check, what happens to a role that is not in the dictionary?",
                                    "choices": [
                                        "It is given admin rights",
                                        "The program stops with an error",
                                        "It gets an empty set, so every action is denied",
                                        "It borrows the mentor permissions",
                                    ],
                                    "correct": 2,
                                    "explanation": "The lookup falls back to an empty set, so an unknown role matches no action at all — that is default-deny.",
                                },
                            ],
                            "estimated_minutes": 5,
                        },
                    ],
                },
                {
                    "title": "The OWASP Top 10",
                    "summary": "The most common web risks, grouped and named.",
                    "lessons": [
                        {
                            "title": "Common web risks",
                            "kind": "text",
                            "summary": "A shared vocabulary for the mistakes attackers rely on.",
                            "paragraphs": [
                                "OWASP maintains the Top 10, a list of the most consequential web application "
                                "risks, so teams can talk about them in a standard way. Broken Access Control "
                                "heads the list: the app does not properly check whether someone may reach a "
                                "resource or action. Injection is next, where untrusted input is sent to an "
                                "interpreter and changes what it does.",
                                "Others include cryptographic failures (leaving data exposed), using components "
                                "with known vulnerabilities, and design or implementation mistakes that let an "
                                "attacker bypass a control. The reassuring part: each risk has a small number of "
                                "well-understood defenses, and later lessons show how to apply them.",
                            ],
                            "bullets": [
                                "Access control: check permission on every request, not just the menu",
                                "Injection: never trust raw input; use the safe API for your database and shell",
                                "Vulnerable components: keep dependencies updated and watch advisories",
                            ],
                            "estimated_minutes": 12,
                        },
                        {
                            "title": "The injection fix: parameterized queries",
                            "kind": "code",
                            "summary": "Separate data from code and the whole class of problem disappears.",
                            "paragraphs": [
                                "The lesson here is not an attack but the defense. When a query is built by "
                                "gluing text together, input can accidentally change its structure. A "
                                "parameterized query sends the SQL and the values to the database separately, so "
                                "the value is always treated as data and can never alter the command.",
                            ],
                            "code": {
                                "language": "sql",
                                "caption": "A safe, reusable statement",
                                "code": """-- %s is a placeholder, not string concatenation.
SELECT id, username
FROM learners
WHERE username = %s;

-- With a DB-API cursor you bind the value as a parameter:
# cursor.execute("SELECT id FROM learners WHERE username = %s", [username])""",
                            },
                            "note": "Always pass values through the driver's parameter list; do not build the query with + or f-strings, even for values that 'look safe'.",
                            "estimated_minutes": 11,
                        },
                        {
                            "title": "Check your understanding",
                            "kind": "quiz",
                            "summary": "Four questions on the OWASP Top 10.",
                            "paragraphs": ["Four questions on the common risks and their fixes."],
                            "questions": [
                                {
                                    "prompt": "Which defense stops injection in a database query?",
                                    "choices": [
                                        "A bigger password policy",
                                        "Parameterized queries that separate data from the statement",
                                        "Hiding the error messages only",
                                        "Using HTTPS",
                                    ],
                                    "correct": 1,
                                    "explanation": "Binding values as parameters means input cannot change the query's structure.",
                                },
                                {
                                    "prompt": "The OWASP Top 10 is best described as:",
                                    "choices": [
                                        "A list of proven exploits to run",
                                        "A standard catalogue of the most important web-app risks and their mitigations",
                                        "A virus definition file",
                                        "A firewall rule set",
                                    ],
                                    "correct": 1,
                                    "explanation": "It is a shared reference for the risks that matter most, aimed at helping defenders.",
                                },
                                {
                                    "prompt": "Why does Broken Access Control head the OWASP list?",
                                    "choices": [
                                        "Because apps fail to check whether the requester may reach a resource or action",
                                        "Because passwords are usually far too short",
                                        "Because databases cannot encrypt their columns",
                                        "Because it only affects static pages",
                                    ],
                                    "correct": 0,
                                    "explanation": "Hiding a link in the menu is not a check, so permission has to be verified on every single request.",
                                },
                                {
                                    "prompt": "How do you limit the risk from components with known vulnerabilities?",
                                    "choices": [
                                        "Rename the dependency in your requirements file",
                                        "Keep dependencies updated and follow security advisories",
                                        "Never use a third-party package again",
                                        "Install every package twice",
                                    ],
                                    "correct": 1,
                                    "explanation": "The weak points are published, so staying updated and reading advisories closes holes that are already known.",
                                },
                            ],
                            "estimated_minutes": 5,
                        },
                    ],
                },
            ],
        },
        {
            "title": "Secure by Default",
            "subtitle": "The daily practices that keep users and data protected.",
            "level": "intermediate",
            "category": "career",
            "duration_hours": 8,
            "objectives": [
                "Store passwords with salted hashes, never in plain text",
                "Validate and encode input at the boundaries",
                "Manage secrets safely and rely on HTTPS in transit",
            ],
            "requirements": ["'Security Fundamentals' or comfortable with the CIA triad and least privilege."],
            "modules": [
                {
                    "title": "Password storage and HTTPS",
                    "summary": "Protecting data at rest and in transit.",
                    "lessons": [
                        {
                            "title": "Hashing versus encryption",
                            "kind": "text",
                            "summary": "Two different tools, used for different jobs.",
                            "paragraphs": [
                                "Hashing turns data into a fixed-length fingerprint that is one-way: you cannot "
                                "reverse it, only compare against it. Encryption turns data into ciphertext that "
                                "you can decrypt again with a key. Passwords should be hashed, not encrypted, "
                                "because the server never needs to read the original back.",
                                "Always salt each password with a unique random value before hashing, and use a "
                                "slow, purpose-built algorithm (bcrypt, scrypt or Argon2) so guessing is "
                                "expensive. For data in transit, HTTPS uses TLS to encrypt the connection and "
                                "authenticate the server, so a password or a token cannot be read or altered on "
                                "the way across the network.",
                            ],
                            "bullets": [
                                "Hashing is one-way; encryption is reversible with a key",
                                "A salt makes two identical passwords hash to different values and defeats lookup tables",
                                "HTTPS is HTTP over TLS: confidential and tamper-proof in transit",
                            ],
                            "estimated_minutes": 13,
                        },
                        {
                            "title": "Hashing and verifying a password",
                            "kind": "code",
                            "summary": "Store the salt and the hash, compare with a safe function.",
                            "paragraphs": [
                                "This shows the shape of the practice: generate a random salt, run a "
                                "deliberately slow key-stretching function, and verify with a constant-time "
                                "comparison. In a real Django project you would call make_password and "
                                "check_password instead, which do exactly this for you.",
                            ],
                            "code": {
                                "language": "python",
                                "caption": "Salted PBKDF2 hashing",
                                "code": """import hashlib
import secrets

def hash_password(password):
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000)
    return salt, digest.hex()

def verify(password, salt, expected_hex):
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000)
    return secrets.compare_digest(digest.hex(), expected_hex)

salt, digest = hash_password("correct horse battery staple")
print(verify("wrong guess", salt, digest))                      # False
print(verify("correct horse battery staple", salt, digest))     # True""",
                            },
                            "note": "compare_digest is constant-time, which avoids leaking information through how long a check takes. Prefer a vetted library over hand-rolled crypto.",
                            "estimated_minutes": 13,
                        },
                        {
                            "title": "Check your understanding",
                            "kind": "quiz",
                            "summary": "Four questions on password storage and HTTPS.",
                            "paragraphs": ["Four questions on protecting data at rest and in transit."],
                            "questions": [
                                {
                                    "prompt": "How should a server store user passwords?",
                                    "choices": [
                                        "Encrypted so it can read them back",
                                        "In plain text for simplicity",
                                        "As salted, slow hashes",
                                        "As a copy of the username",
                                    ],
                                    "correct": 2,
                                    "explanation": "Hashing is one-way and, with a salt and slow algorithm, resists guessing.",
                                },
                                {
                                    "prompt": "What does HTTPS primarily protect?",
                                    "choices": [
                                        "Data at rest on the disk",
                                        "Data in transit between the browser and the server",
                                        "Passwords stored in the database",
                                        "The server's CPU usage",
                                    ],
                                    "correct": 1,
                                    "explanation": "TLS encrypts the connection so traffic cannot be read or altered en route.",
                                },
                                {
                                    "prompt": "Why use a deliberately slow algorithm such as bcrypt or Argon2 for passwords?",
                                    "choices": [
                                        "So nobody can ever verify a password",
                                        "To make guessing each password expensive",
                                        "Because fast hashes are not fixed-length",
                                        "So the hash hides the length of the password",
                                    ],
                                    "correct": 1,
                                    "explanation": "One slow check costs a real user nothing noticeable, but it multiplies across every guess an attacker has to try.",
                                },
                                {
                                    "prompt": "What does comparing hashes with secrets.compare_digest buy you?",
                                    "choices": [
                                        "A constant-time check that leaks nothing through how long it takes",
                                        "A way to decrypt the stored hash",
                                        "A guarantee that two passwords are identical",
                                        "A fresh salt on every login",
                                    ],
                                    "correct": 0,
                                    "explanation": "Timing how long a check takes can reveal how much of a guess matched, so a constant-time comparison removes that signal.",
                                },
                            ],
                            "estimated_minutes": 5,
                        },
                    ],
                },
                {
                    "title": "Input validation and secrets",
                    "summary": "Treat all input as hostile and keep secrets where they belong.",
                    "lessons": [
                        {
                            "title": "Validate input, protect secrets",
                            "kind": "text",
                            "summary": "Boundaries are where you decide what is allowed.",
                            "paragraphs": [
                                "The rule at every boundary is simple: validate against what you expect, then "
                                "encode for where the value goes next. Accept a known set of values or a strict "
                                "format rather than trying to block bad input, because attackers invent bad input "
                                "faster than you can list it. When you render text as HTML, output-encode it so "
                                "it stays text and never becomes markup.",
                                "Secrets — keys, tokens, database passwords — belong in environment variables or "
                                "a secret manager, never hard-coded in source or committed to git. Give the "
                                "smallest possible scope to each credential, and rotate any that might have "
                                "leaked, because a secret in history is effectively public once it has been "
                                "pushed.",
                            ],
                            "bullets": [
                                "Whitelist what is allowed; do not just blacklist what looks bad",
                                "Output-encode untrusted text before rendering it",
                                "Rotate a leaked secret immediately and remove it from version control",
                            ],
                            "estimated_minutes": 12,
                        },
                        {
                            "title": "Handling a secret file",
                            "kind": "code",
                            "summary": "Keep secrets out of git and readable only by you.",
                            "paragraphs": [
                                "The pattern in practice: put the .env file in .gitignore, restrict its "
                                "permissions, store the value there, and have the application read it from the "
                                "environment at runtime instead of a hard-coded string.",
                            ],
                            "code": {
                                "language": "bash",
                                "caption": "A secret file that never reaches git",
                                "code": """# Keep secrets out of source control and limit who can read the file.
echo ".env" >> .gitignore
chmod 600 .env
echo "DATABASE_NAME=codeher" >> .env

# The app reads it at runtime, for example os.environ["DATABASE_NAME"],
# instead of hard-coding a value in a committed file.
# Rotate any credential that may have leaked, then remove it from history.""",
                            },
                            "note": "chmod 600 means only the file's owner can read or write it, which is the minimum you want for a file holding secrets.",
                            "estimated_minutes": 11,
                        },
                        {
                            "title": "Check your understanding",
                            "kind": "quiz",
                            "summary": "Four questions on validation and secrets.",
                            "paragraphs": ["Four questions to finish the cybersecurity path."],
                            "questions": [
                                {
                                    "prompt": "The safer input strategy is to:",
                                    "choices": [
                                        "Blacklist characters you dislike",
                                        "Whitelist the values or format you actually expect",
                                        "Accept anything and trust the user",
                                        "Remove all punctuation",
                                    ],
                                    "correct": 1,
                                    "explanation": "Allowing a known-good set is far more reliable than chasing every bad input.",
                                },
                                {
                                    "prompt": "What should you do with a credential you think has leaked?",
                                    "choices": [
                                        "Leave it; it is probably fine",
                                        "Rotate it and remove it from version control",
                                        "Put it in the README",
                                        "Log it on every request",
                                    ],
                                    "correct": 1,
                                    "explanation": "Assume a leaked secret is public: replace it and clear it from history.",
                                },
                                {
                                    "prompt": "Why output-encode untrusted text before rendering it inside HTML?",
                                    "choices": [
                                        "So it stays text and never becomes markup",
                                        "So the page finishes loading sooner",
                                        "So the value is safe to store in the database",
                                        "So browsers can cache the response",
                                    ],
                                    "correct": 0,
                                    "explanation": "Encoding turns characters that look like tags into plain text, so the browser displays them instead of acting on them.",
                                },
                                {
                                    "prompt": "What does chmod 600 on a .env file do?",
                                    "choices": [
                                        "Compresses the file before you commit it",
                                        "Allows only the file's owner to read or write it",
                                        "Marks the file as read-only for everyone",
                                        "Hides the file from git status",
                                    ],
                                    "correct": 1,
                                    "explanation": "600 grants read and write to the owner alone, the minimum you want for a file that holds secrets.",
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
