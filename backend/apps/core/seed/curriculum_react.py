"""Sample curriculum, part C: the React path.

This is clearly labelled demonstration content — it is what makes CodeHer useful
immediately after `manage.py seed`. Replace or extend it through the admin console.
"""

REACT = {
    "title": "React",
    "slug": "react",
    "level": "beginner",
    "color": "#22d3ee",
    "icon": "Atom",
    "description": "Go from your first JSX element to a working multi-page React app that talks to real data. "
    "You will learn how components, hooks and routing fit together — and why we always clean up after ourselves.",
    "courses": [
        {
            "title": "React Essentials: Components, Props and State",
            "subtitle": "The mental model behind every React app, built one small component at a time.",
            "level": "beginner",
            "category": "react",
            "duration_hours": 12,
            "objectives": [
                "Explain the problem React solves and when a plain HTML page is the better tool",
                "Write function components that pass data down with props and keep local data with useState",
                "Render lists with a stable key and build a controlled form that responds to events",
            ],
            "requirements": [
                "JavaScript basics: functions, objects, arrays and template literals.",
                "A code editor and Node.js so you can start a Vite dev server with npm run dev.",
            ],
            "modules": [
                {
                    "title": "Thinking in components",
                    "summary": "What React is, how JSX works and how to render a list safely.",
                    "lessons": [
                        {
                            "title": "What React is and when to reach for it",
                            "kind": "text",
                            "summary": "Components, declarative UI and the sync problem React removes.",
                            "paragraphs": [
                                "React is a JavaScript library for building user interfaces out of components — "
                                "small, reusable functions that describe how a piece of the screen should look for "
                                "a given set of data. Instead of reaching into the page and mutating it yourself, "
                                "you declare the result you want and React keeps the real DOM in sync when the data "
                                "changes.",
                                "That sync is the whole point. On a plain page, when a learner edits their profile "
                                "name you have to find every place it appears and update each one — and you will "
                                "forget one. With React the name lives in a single place; change it and every "
                                "component showing it re-renders automatically. Reach for React when your UI has "
                                "state that changes and many places depend on it; a static brochure page still does "
                                "not need it.",
                            ],
                            "bullets": [
                                "A component is just a function that returns markup — there is no alien syntax to fear",
                                "You describe what the UI should look like; React works out how to update the DOM",
                                "Choose React for data-driven, interactive screens, not for a page that never changes",
                            ],
                            "note": "If you already learned 'DOM manipulation', this is not that skill being deleted — it is moving up a level of abstraction.",
                            "estimated_minutes": 10,
                        },
                        {
                            "title": "JSX, expressions and rendering a list with a key",
                            "kind": "code",
                            "summary": "Write markup in JavaScript and map an array to keyed rows.",
                            "paragraphs": [
                                "JSX looks like HTML written inside JavaScript, and it is how a component describes "
                                "its output. Curly braces let you drop any expression into that markup — {skill.name}, "
                                "{items.length}, even {isLoading ? 'Loading' : 'Ready'} — which is why React feels "
                                "like one language instead of a template bolted onto logic.",
                                "To render a list you map over an array and return an element per item. React then "
                                "needs a key: a stable, unique value for each row. Give it the item's id, never its "
                                "position, so that when the list re-sorts React can tell which row is which instead "
                                "of rebuilding the wrong ones.",
                            ],
                            "bullets": [
                                "In JSX the class attribute becomes className and for becomes htmlFor",
                                "A component returns one top-level element — wrap siblings in a fragment <> ... </>",
                                "Use a stable key like skill.id; index-based keys cause subtle bugs when the list changes",
                            ],
                            "code": {
                                "language": "javascript",
                                "caption": "A component, expression interpolation and a keyed list",
                                "code": """function SkillBadge({ skill }) {
  return (
    <span className="badge">
      {skill.name} - level {skill.level}
    </span>
  );
}

function SkillList({ skills }) {
  return (
    <ul className="skill-list">
      {skills.map((skill) => (
        <li key={skill.id}>
          <SkillBadge skill={skill} />
        </li>
      ))}
    </ul>
  );
}

const skills = [
  { id: 's1', name: 'HTML', level: 'confident' },
  { id: 's2', name: 'CSS', level: 'learning' },
];

// <SkillList skills={skills} /> renders one keyed row per skill.
""",
                            },
                            "note": "The key prop is special: React uses it internally, so your component never receives it as an ordinary prop.",
                            "estimated_minutes": 15,
                        },
                        {
                            "title": "Check your understanding",
                            "kind": "quiz",
                            "summary": "Four questions on components, JSX and keys.",
                            "questions": [
                                {
                                    "prompt": "What problem does React mainly solve?",
                                    "choices": [
                                        "Making pages load faster by caching files",
                                        "Rendering HTML only on the server",
                                        "Keeping the interface in sync with changing data declaratively",
                                        "Replacing CSS so you never style anything",
                                    ],
                                    "correct": 2,
                                    "explanation": "You declare the UI for a given state and React updates the DOM when that state changes.",
                                },
                                {
                                    "prompt": "In JSX, how do you embed a JavaScript value?",
                                    "choices": ["<%= value %>", "{value}", "{{value}}", "$value"],
                                    "correct": 1,
                                    "explanation": "Single curly braces evaluate any JavaScript expression inside JSX.",
                                },
                                {
                                    "prompt": "Why does a rendered list need a stable key?",
                                    "choices": [
                                        "To style each row a different colour",
                                        "So React can track which item is which across re-renders",
                                        "Keys are required by the browser itself",
                                        "To sort the array for you",
                                    ],
                                    "correct": 1,
                                    "explanation": "A stable id lets React reuse the right rows when the list re-orders instead of rebuilding wrong ones.",
                                },
                                {
                                    "prompt": "Which is a good reason NOT to use React?",
                                    "choices": [
                                        "The page is a static brochure with no interactivity",
                                        "The app has a lot of shared state",
                                        "You want to reuse components",
                                        "You are fetching data from an API",
                                    ],
                                    "correct": 0,
                                    "explanation": "A page that never changes does not need a component model — plain HTML stays simpler.",
                                },
                            ],
                            "estimated_minutes": 6,
                        },
                    ],
                },
                {
                    "title": "Data that changes: props and state",
                    "summary": "Props flow down, state lives locally, and both update the screen.",
                    "lessons": [
                        {
                            "title": "Props versus state and the useState hook",
                            "kind": "code",
                            "summary": "Read-only props, owned state, and immutable updates.",
                            "paragraphs": [
                                "Props are the values a parent hands down to a child; inside the child they are "
                                "read-only, like function arguments. State is data the component owns and can "
                                "change, and you get it from the useState hook, which returns the current value "
                                "and a setter function.",
                                "The golden rule is immutability. Never change a state object or array in place — "
                                "call the setter with a brand-new value instead. React decides whether to re-render "
                                "by comparing the old reference with the new one, so mutating the same array can "
                                "silently skip the update everyone is waiting for.",
                            ],
                            "bullets": [
                                "useState(initial) returns [value, setValue] — give the setter a clear name",
                                "Build the next value from the old one: setTopics(topics.map(...)) or setCount((c) => c + 1)",
                                "Spread copies objects, so { ...topic, done: true } leaves the original untouched",
                            ],
                            "code": {
                                "language": "javascript",
                                "caption": "Props in, immutable state updates out",
                                "code": """import { useState } from 'react';

// Props arrive from the parent and stay read-only inside the child.
// State is created here with useState and changes only through its setter.
function TopicList({ initialTopics }) {
  const [topics, setTopics] = useState(initialTopics);

  function complete(id) {
    // Immutable update: build a NEW array with a NEW object for that item.
    setTopics(topics.map((topic) => (topic.id === id ? { ...topic, done: true } : topic)));
  }

  return (
    <ul>
      {topics.map((topic) => (
        <li key={topic.id}>
          {topic.name} {topic.done ? ' - done' : ''}
          {!topic.done && (
            <button onClick={() => complete(topic.id)}>Mark done</button>
          )}
        </li>
      ))}
    </ul>
  );
}
""",
                            },
                            "note": "setCount(count + 1) also works, but the updater form setCount((c) => c + 1) is safer when several updates stack before the next render.",
                            "estimated_minutes": 14,
                        },
                        {
                            "title": "Handling events and controlled form inputs",
                            "kind": "code",
                            "summary": "onClick and onChange handlers, preventDefault, and value from state.",
                            "paragraphs": [
                                "React wires events through props like onClick and onChange, and your handler "
                                "receives a cross-browser event object. Forms need event.preventDefault() to stop "
                                "the page reloading, and inputs are usually controlled — their value comes straight "
                                "from state, so React is always the single source of truth.",
                                "Typing in a controlled input fires onChange, which updates state, which re-renders "
                                "the input with the new value. That little round trip costs some effort but buys you "
                                "validation, formatting and one obvious place to read the value on submit.",
                            ],
                            "bullets": [
                                "React event props are camelCase: onClick, not the HTML onclick",
                                "value plus onChange makes an input controlled; omit value and it becomes uncontrolled",
                                "Keep the label tied to the field with htmlFor and id for keyboard and screen-reader users",
                            ],
                            "code": {
                                "language": "javascript",
                                "caption": "A controlled search field",
                                "code": """import { useState } from 'react';

function SearchField({ onSearch }) {
  // A controlled input: state owns the value, the input reflects it.
  const [query, setQuery] = useState('');

  function handleChange(event) {
    setQuery(event.target.value);
  }

  function handleSubmit(event) {
    event.preventDefault(); // stop the native form submission that reloads the page
    if (query.trim()) {
      onSearch(query.trim());
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <label htmlFor="q">Search courses</label>
      <input id="q" type="search" value={query} onChange={handleChange} />
      <button type="submit">Search</button>
    </form>
  );
}
""",
                            },
                            "estimated_minutes": 15,
                        },
                        {
                            "title": "Check your understanding",
                            "kind": "quiz",
                            "summary": "Four questions on props, state and controlled inputs.",
                            "questions": [
                                {
                                    "prompt": "Which statement about props and state is true?",
                                    "choices": [
                                        "A component rewrites its own props when it likes",
                                        "State is read-only and props are mutable",
                                        "Props are read-only in the child; state is owned and updated via its setter",
                                        "Both can be reassigned freely inside the component",
                                    ],
                                    "correct": 2,
                                    "explanation": "Props come in read-only from the parent; state is local and only changes through its setter.",
                                },
                                {
                                    "prompt": "Why treat React state as immutable?",
                                    "choices": [
                                        "JavaScript cannot change objects at all",
                                        "Mutating in place can leave the reference equal, so React may skip the re-render",
                                        "setState is a promise that must be awaited",
                                        "Immutability makes the bundle smaller",
                                    ],
                                    "correct": 1,
                                    "explanation": "React compares the previous reference to the new one; changing in place keeps it equal and the screen never updates.",
                                },
                                {
                                    "prompt": "What makes a text input 'controlled'?",
                                    "choices": [
                                        "It has a name attribute",
                                        "Its value comes from React state and updates through onChange",
                                        "It is permanently disabled",
                                        "It shows placeholder text",
                                    ],
                                    "correct": 1,
                                    "explanation": "value bound to state plus an onChange handler means React is the source of truth.",
                                },
                                {
                                    "prompt": "In a form submit handler, what does event.preventDefault() do?",
                                    "choices": [
                                        "Stops the event bubbling to parents",
                                        "Prevents the browser's default page-reloading submission",
                                        "Clears every input value",
                                        "Disables the submit button",
                                    ],
                                    "correct": 1,
                                    "explanation": "It cancels the native submit (a full reload) so your JavaScript can handle it instead.",
                                },
                            ],
                            "estimated_minutes": 7,
                        },
                    ],
                },
            ],
        },
        {
            "title": "React in a Real App: Hooks, Data and Routing",
            "subtitle": "Effects that clean up after themselves, real network data, pages and a production build.",
            "level": "intermediate",
            "category": "react",
            "duration_hours": 14,
            "objectives": [
                "Synchronise components with the outside world using useEffect, a dependency array you can reason about, and real cleanup",
                "Fetch data with explicit loading, error and success states, then lift shared state to a common parent",
                "Route between pages with React Router, validate forms accessibly, and ship a production Vite build",
            ],
            "requirements": [
                "Completion of 'React Essentials: Components, Props and State', or confidence with useState and props.",
                "A local Vite React project you can run with npm run dev.",
            ],
            "modules": [
                {
                    "title": "Effects and data",
                    "summary": "useEffect with cleanup, and lifting state across a small app.",
                    "lessons": [
                        {
                            "title": "useEffect, the dependency array and cleanup",
                            "kind": "code",
                            "summary": "Fetch once, show loading/error/ready, and abort on unmount.",
                            "paragraphs": [
                                "useState holds your data; useEffect is where you talk to the outside world — a "
                                "network request, a subscription, the browser. It runs after render, and a "
                                "dependency array tells React when to run it again: an empty array means 'once, "
                                "after the first render', while listing a value re-runs the effect when it changes.",
                                "The trick that separates a solid effect from a buggy one is cleanup. When you "
                                "fetch inside an effect, create an AbortController and abort it in the function you "
                                "return. If the component unmounts or the dependency changes mid-flight, the "
                                "abandoned request is cancelled instead of calling setState on a component that is "
                                "already gone.",
                            ],
                            "bullets": [
                                "Track status explicitly (loading, error, ready) so the UI always has something to show",
                                "Return a cleanup function to cancel work — that is exactly what the AbortController signal is for",
                                "An empty dependency array [] runs the effect once; add a value to re-run when it changes",
                            ],
                            "code": {
                                "language": "javascript",
                                "caption": "Fetching with loading, error and abortable cleanup",
                                "code": """import { useEffect, useState } from 'react';

function MentorDirectory() {
  const [mentors, setMentors] = useState([]);
  const [status, setStatus] = useState('loading'); // loading | error | ready
  const [error, setError] = useState(null);

  useEffect(() => {
    // Cancel the request if the component unmounts or the effect re-runs.
    const controller = new AbortController();

    async function load() {
      try {
        setStatus('loading');
        const response = await fetch('/api/mentors/', { signal: controller.signal });
        if (!response.ok) {
          throw new Error(`Request failed: ${response.status}`);
        }
        setMentors(await response.json());
        setStatus('ready');
      } catch (err) {
        if (err.name !== 'AbortError') {
          setError(err.message);
          setStatus('error');
        }
      }
    }

    load();
    return () => controller.abort(); // cleanup: runs on unmount and before a re-run
  }, []); // empty dependency array = run once after the first render

  return (
    <section aria-live="polite">
      {status === 'loading' && <p>Loading mentors...</p>}
      {status === 'error' && <p>Something went wrong: {error}</p>}
      {status === 'ready' && (
        <ul>
          {mentors.map((mentor) => (
            <li key={mentor.id}>{mentor.name}</li>
          ))}
        </ul>
      )}
    </section>
  );
}
""",
                            },
                            "note": "The aria-live region announces 'Loading' and then the results to a screen reader, without stealing focus from what the person is doing.",
                            "estimated_minutes": 18,
                        },
                        {
                            "title": "Lifting state and the useRef escape hatch",
                            "kind": "code",
                            "summary": "Share one source of truth and touch the DOM only when you must.",
                            "paragraphs": [
                                "When two components need the same data, move that state up to their closest shared "
                                "parent and pass it down as props. One source of truth keeps the list highlight and "
                                "the detail panel in step without either one trying to remember the other.",
                                "Sometimes you genuinely need a DOM node — to focus something after a change, or to "
                                "read a value without re-rendering. That is what useRef is for: a mutable box that "
                                "survives renders and never triggers a re-render when you write to it. Treat it as "
                                "the escape hatch it is, and reach for state first.",
                            ],
                            "bullets": [
                                "Lift state to the closest common parent so sibling components stay synchronised",
                                "useRef returns an object with a .current you can read and write across renders",
                                "Focusing with ref.current?.focus() is a real accessibility win on selection and route changes",
                            ],
                            "code": {
                                "language": "javascript",
                                "caption": "One source of truth, plus a ref for focus",
                                "code": """import { useRef, useState } from 'react';

// State lifted to the shared parent so the list and the panel always agree.
function CourseBrowser({ courses }) {
  const [selectedId, setSelectedId] = useState(courses[0]?.id ?? null);
  const panelRef = useRef(null); // a DOM node we focus imperatively, kept out of state

  function choose(id) {
    setSelectedId(id);
    // Move focus without storing a DOM node in React state.
    requestAnimationFrame(() => panelRef.current?.focus());
  }

  const selected = courses.find((course) => course.id === selectedId);

  return (
    <div className="browser">
      <ul>
        {courses.map((course) => (
          <li key={course.id}>
            <button onClick={() => choose(course.id)} aria-pressed={course.id === selectedId}>
              {course.title}
            </button>
          </li>
        ))}
      </ul>

      <section ref={panelRef} tabIndex={-1} aria-live="polite">
        {selected && <h3>{selected.title}</h3>}
      </section>
    </div>
  );
}
""",
                            },
                            "estimated_minutes": 14,
                        },
                        {
                            "title": "Check your understanding",
                            "kind": "quiz",
                            "summary": "Four questions on effects, fetching and refs.",
                            "questions": [
                                {
                                    "prompt": "What does an empty dependency array [] mean for useEffect?",
                                    "choices": [
                                        "The effect runs on every single render",
                                        "The effect runs once, after the first render",
                                        "The effect never runs",
                                        "The effect runs before the component renders",
                                    ],
                                    "correct": 1,
                                    "explanation": "An empty array tells React the effect has no dependencies, so it runs one time after mount.",
                                },
                                {
                                    "prompt": "Why return a cleanup function when you fetch inside an effect?",
                                    "choices": [
                                        "To make the network request go faster",
                                        "To cancel work (e.g. abort) if the component unmounts or the effect re-runs",
                                        "Cleanup is just required syntax with no purpose",
                                        "To free CSS memory",
                                    ],
                                    "correct": 1,
                                    "explanation": "Aborting prevents setState on an unmounted component and avoids two responses racing each other.",
                                },
                                {
                                    "prompt": "'Lifting state up' means:",
                                    "choices": [
                                        "Moving shared state to the closest common parent so children can pass data",
                                        "Deleting the state entirely",
                                        "Storing the state in localStorage",
                                        "Returning state from every event handler",
                                    ],
                                    "correct": 0,
                                    "explanation": "One parent owns the truth and passes it down, so siblings stay in sync.",
                                },
                                {
                                    "prompt": "useRef is best described as:",
                                    "choices": [
                                        "A hook that re-renders the component when its value changes",
                                        "A mutable box that persists across renders and can hold a DOM node, without re-rendering",
                                        "A drop-in replacement for useState",
                                        "A feature only available to class components",
                                    ],
                                    "correct": 1,
                                    "explanation": "Writing to ref.current does not trigger a render, which is exactly why it suits DOM handles.",
                                },
                            ],
                            "estimated_minutes": 8,
                        },
                    ],
                },
                {
                    "title": "Pages, forms and shipping",
                    "summary": "Routing with React Router, accessible validation and a production Vite build.",
                    "lessons": [
                        {
                            "title": "Client-side routing with React Router",
                            "kind": "code",
                            "summary": "Routes, NavLink, useParams, protected pages and focus management.",
                            "paragraphs": [
                                "React Router swaps which component is showing while the URL changes, without a full "
                                "page reload. You declare routes once; NavLink renders the links and marks the "
                                "current one, and useParams hands you the dynamic parts of the path, such as the "
                                "course slug in /courses/:slug.",
                                "A protected route is just a component: if there is no session, render <Navigate to='/login' /> "
                                "instead of the page. Because client-side navigation never reloads the document, you "
                                "also have to move focus yourself — a small effect that focuses the main region on "
                                "each route change keeps keyboard and screen-reader users oriented.",
                            ],
                            "bullets": [
                                "NavLink adds an active class and sets aria-current automatically for the matching link",
                                "useParams() reads dynamic segments like slug from a route such as /courses/:slug",
                                "Guard a route by rendering <Navigate> from a wrapper and storing the origin to return to",
                                "Focus the main region by calling ref.current?.focus() in an effect keyed to location.pathname",
                            ],
                            "code": {
                                "language": "javascript",
                                "caption": "Routes, a guarded route and focus on navigation",
                                "code": """import { useEffect, useRef } from 'react';
import {
  NavLink, Route, Routes, useParams, Navigate, useLocation,
} from 'react-router-dom';

function NavBar() {
  return (
    <nav aria-label="Primary">
      {/* NavLink sets the active state and aria-current for us */}
      <NavLink to="/" end>Home</NavLink>
      <NavLink to="/courses">Courses</NavLink>
      <NavLink to="/dashboard">Dashboard</NavLink>
    </nav>
  );
}

function CourseDetail() {
  const { slug } = useParams(); // /courses/:slug exposes slug here
  return <h1>Course page for {slug}</h1>;
}

// A protected route: render the child, or redirect when there is no session.
function RequireAuth({ isAuthed, children }) {
  const location = useLocation();
  if (!isAuthed) {
    // Remember where they were headed so login can return them there.
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  return children;
}

function App({ isAuthed }) {
  const mainRef = useRef(null);
  const location = useLocation();

  // Accessibility: move focus to the main region on every route change.
  useEffect(() => {
    mainRef.current?.focus();
  }, [location.pathname]);

  return (
    <>
      <NavBar />
      <main ref={mainRef} tabIndex={-1}>
        <Routes>
          <Route path="/" element={<h1>Welcome</h1>} />
          <Route path="/courses/:slug" element={<CourseDetail />} />
          <Route
            path="/dashboard"
            element={
              <RequireAuth isAuthed={isAuthed}>
                <h1>Your dashboard</h1>
              </RequireAuth>
            }
          />
        </Routes>
      </main>
    </>
  );
}
""",
                            },
                            "note": "tabIndex={-1} lets a <main> take programmatic focus without joining the normal tab order — the standard way to announce a new page to a screen reader.",
                            "estimated_minutes": 16,
                        },
                        {
                            "title": "Accessible form validation and a production Vite build",
                            "kind": "code",
                            "summary": "Validate in React, announce errors, then build and preview the bundle.",
                            "paragraphs": [
                                "A form that only reports errors after a full reload feels hostile. Validate on "
                                "submit inside React, keep the messages in state, and connect each error to its "
                                "field with aria-invalid and aria-describedby, so a screen reader reads the problem "
                                "in context instead of dumping a list at the top of the page.",
                                "To ship it, Vite bundles your app into a dist folder with npm run build. Run npm run "
                                "preview to serve that exact production output locally, because a few bugs only show "
                                "up in the built bundle. Anything the browser may read has to be a VITE_-prefixed "
                                "variable — import.meta.env.VITE_API_URL — and never holds a secret, since the bundle "
                                "is public. If the site lives in a subfolder, set base in vite.config.js so asset "
                                "paths resolve.",
                            ],
                            "bullets": [
                                "npm run build produces dist/; npm run preview serves it to catch production-only issues",
                                "Only VITE_* variables reach the browser via import.meta.env — never put secrets there",
                                "Set base in vite.config.js when the app deploys under a subdirectory",
                                "role='alert' announces validation errors without stealing focus",
                            ],
                            "code": {
                                "language": "javascript",
                                "caption": "A validated, announced form",
                                "code": """import { useState } from 'react';

function GoalForm({ onSubmit }) {
  const [goal, setGoal] = useState('');
  const [error, setError] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  function handleSubmit(event) {
    event.preventDefault();

    if (goal.trim().length < 5) {
      setError('Please write at least 5 characters.');
      return;
    }

    setError('');
    setIsSaving(true);
    onSubmit(goal.trim()).finally(() => setIsSaving(false));
  }

  return (
    <form onSubmit={handleSubmit} noValidate>
      <label htmlFor="goal">Weekly goal</label>
      <input
        id="goal"
        value={goal}
        onChange={(event) => setGoal(event.target.value)}
        aria-invalid={error ? 'true' : undefined}
        aria-describedby={error ? 'goal-error' : undefined}
      />

      {/* Announced to screen readers the moment the text appears. */}
      {error && <p id="goal-error" role="alert">{error}</p>}

      <button type="submit" disabled={isSaving}>
        {isSaving ? 'Saving...' : 'Save goal'}
      </button>
    </form>
  );
}
""",
                            },
                            "note": "The disabled button showing 'Saving...' is the considerate half of this UX; the aria-invalid wiring is the accessible half — real apps need both.",
                            "estimated_minutes": 16,
                        },
                        {
                            "title": "Check your understanding",
                            "kind": "quiz",
                            "summary": "Four questions on routing, validation and deploying.",
                            "questions": [
                                {
                                    "prompt": "What does useParams() give you?",
                                    "choices": [
                                        "The full browser history stack",
                                        "The dynamic segments of the matched route, like slug from /courses/:slug",
                                        "A function to programmatically navigate",
                                        "Only the current query-string values",
                                    ],
                                    "correct": 1,
                                    "explanation": "useParams returns an object keyed by each dynamic path segment for the active route.",
                                },
                                {
                                    "prompt": "NavLink is preferred over a plain <a> for app links because it:",
                                    "choices": [
                                        "Loads noticeably faster",
                                        "Adds the active styling and sets aria-current automatically",
                                        "Disables the router",
                                        "Works even when JavaScript is off",
                                    ],
                                    "correct": 1,
                                    "explanation": "It knows which link matches the current route and exposes that to styling and assistive tech.",
                                },
                                {
                                    "prompt": "Which environment variable reaches a Vite client bundle?",
                                    "choices": ["API_SECRET", "VITE_API_URL", "DATABASE_URL", "A variable with any name"],
                                    "correct": 1,
                                    "explanation": "Only VITE_-prefixed names are inlined into client code; secrets must stay server-side.",
                                },
                                {
                                    "prompt": "After `npm run build`, which command checks the production bundle locally?",
                                    "choices": ["npm run dev", "npm run preview", "npm start", "npm audit"],
                                    "correct": 1,
                                    "explanation": "preview serves the dist output like production, so build-only bugs (and a wrong base path) surface here.",
                                },
                            ],
                            "estimated_minutes": 8,
                        },
                    ],
                },
            ],
        },
    ],
}
