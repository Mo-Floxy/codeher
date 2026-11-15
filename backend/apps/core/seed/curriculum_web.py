"""Sample curriculum, part A: the web foundation paths.

This is clearly labelled demonstration content — it is what makes CodeHer useful
immediately after `manage.py seed`. Replace or extend it through the admin console.
"""

HTML_CSS = {
    "title": "HTML & CSS Fundamentals",
    "slug": "html-css-fundamentals",
    "level": "beginner",
    "color": "#ec4899",
    "icon": "FileCode2",
    "description": "Structure a page properly and style it with modern CSS. You will build real, "
    "accessible layouts from your first tag to a responsive component.",
    "courses": [
        {
            "title": "Semantic HTML: Pages That Make Sense",
            "subtitle": "Mark up content so people, screens and search engines all understand it.",
            "level": "beginner",
            "category": "web",
            "duration_hours": 6,
            "objectives": [
                "Choose the right element for the job instead of defaulting to div",
                "Build a page outline with landmarks a screen reader can navigate",
                "Add images, links and forms that are accessible by keyboard",
            ],
            "requirements": ["A browser and any text editor. No previous experience needed."],
            "modules": [
                {
                    "title": "The document",
                    "summary": "How a page is put together, from doctype to body.",
                    "lessons": [
                        {
                            "title": "Anatomy of an HTML document",
                            "kind": "text",
                            "summary": "The five parts every page needs and what each one is for.",
                            "paragraphs": [
                                "HTML describes meaning, not appearance. When you write <h1>, you are telling "
                                "the browser 'this is the main topic', and every assistive technology uses that "
                                "clue to build an outline the reader can jump around in.",
                                "A document starts with a doctype, then a root <html> element with a lang "
                                "attribute. The <head> carries metadata that never renders: the character set, "
                                "the title shown in the tab, and links to stylesheets. Everything a person can "
                                "actually see lives in the <body>.",
                            ],
                            "bullets": [
                                "<!DOCTYPE html> switches the browser into standards mode",
                                "lang='en' lets screen readers pick the right pronunciation",
                                "<meta charset='utf-8'> must be the first thing inside <head>",
                                "One <h1> per page: it is the document's title, not the biggest text",
                            ],
                            "code": {
                                "language": "html",
                                "caption": "A minimal, valid starting point",
                                "code": "<!DOCTYPE html>\n<html lang=\"en\">\n  <head>\n    <meta charset=\"utf-8\" />\n    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />\n    <title>My first page</title>\n  </head>\n  <body>\n    <h1>Hello, world</h1>\n  </body>\n</html>",
                            },
                            "estimated_minutes": 12,
                        },
                        {
                            "title": "Landmarks and headings",
                            "kind": "text",
                            "summary": "Give a page a skeleton people can navigate.",
                            "paragraphs": [
                                "Before CSS existed, pages were walls of text. Landmark elements — <header>, "
                                "<nav>, <main>, <aside>, <footer> — turn a flat page into a region map. A "
                                "screen reader user can press a single key and hop straight to <main>, skipping "
                                "your navigation entirely.",
                                "Headings are the other half. They must nest without gaps: an <h3> only makes "
                                "sense underneath an <h2>. Do not pick a heading level because it looks the "
                                "right size — that is what CSS is for.",
                            ],
                            "note": "Rule of thumb: if you are reaching for <div class='header'>, a real landmark element almost certainly exists.",
                            "code": {
                                "language": "html",
                                "caption": "A page skeleton",
                                "code": "<body>\n  <header>\n    <h1>CodeHer</h1>\n    <nav aria-label=\"Main\">\n      <a href=\"/learning\">Learning</a>\n      <a href=\"/community\">Community</a>\n    </nav>\n  </header>\n\n  <main>\n    <h2>Your journey in tech starts here</h2>\n    <section>\n      <h3>Courses</h3>\n    </section>\n  </main>\n\n  <footer>\n    <p>Built with the CodeHer community.</p>\n  </footer>\n</body>",
                            },
                            "estimated_minutes": 15,
                        },
                        {
                            "title": "Check your understanding",
                            "kind": "quiz",
                            "summary": "Four questions on document structure.",
                            "questions": [
                                {
                                    "prompt": "Which element should contain the primary content of a page?",
                                    "choices": ["<section>", "<main>", "<div id='content'>", "<article>"],
                                    "correct": 1,
                                    "explanation": "<main> is unique per page and is where screen readers send people to skip the chrome.",
                                },
                                {
                                    "prompt": "What happens if you skip from an <h2> straight to an <h4>?",
                                    "choices": [
                                        "Nothing — levels are only visual",
                                        "The page fails to render",
                                        "The outline has a gap, which confuses assistive technology",
                                        "Search engines hide the <h4>",
                                    ],
                                    "correct": 2,
                                    "explanation": "Heading levels describe nesting depth, so a gap means the document structure is wrong.",
                                },
                                {
                                    "prompt": "Where does the <title> element belong?",
                                    "choices": ["At the start of <body>", "Inside <head>", "Inside <footer>", "Anywhere is fine"],
                                    "correct": 1,
                                    "explanation": "<title> is metadata about the document, so it lives in the head.",
                                },
                                {
                                    "prompt": "Why is <nav aria-label='Main'> better than <div class='nav'>?",
                                    "choices": [
                                        "It loads faster",
                                        "It exposes a navigable landmark region with a name",
                                        "Div elements are deprecated",
                                        "It automatically styles the links",
                                    ],
                                    "correct": 1,
                                    "explanation": "The label gives the landmark an accessible name people hear when they list regions.",
                                },
                            ],
                            "estimated_minutes": 6,
                        },
                    ],
                },
                {
                    "title": "Media, links and forms",
                    "summary": "The interactive parts of a page done accessibly.",
                    "lessons": [
                        {
                            "title": "Images with alt text that earns its place",
                            "kind": "text",
                            "summary": "Describe the purpose, not the pixels.",
                            "paragraphs": [
                                "Alt text answers 'what would I miss if this image were not here?'. A decorative "
                                "background shape is not informative, so it gets alt='' — the empty string, which "
                                "silently removes it from the reading order. A chart showing a trend is informative, "
                                "so its alt text states the trend.",
                                "Always set width and height (or use aspect-ratio in CSS). The browser then reserves "
                                "the space before the file arrives, and the page stops jumping around while it loads.",
                            ],
                            "code": {
                                "language": "html",
                                "caption": "Informative versus decorative images",
                                "code": "<!-- Carries meaning: describe what it conveys -->\n<img src=\"/charts/progress.svg\" width=\"640\" height=\"360\"\n     alt=\"Course completions doubled between March and June 2026\" />\n\n<!-- Purely decorative: empty alt hides it from readers -->\n<img src=\"/shapes/blob.svg\" width=\"120\" height=\"120\" alt=\"\" aria-hidden=\"true\" />",
                            },
                            "estimated_minutes": 10,
                        },
                        {
                            "title": "Links, buttons and when each belongs",
                            "kind": "text",
                            "summary": "A link navigates; a button acts.",
                            "paragraphs": [
                                "Use <a href> when the action changes the URL or moves somewhere, and <button> "
                                "when it performs an action on the current page, like opening a dialog or saving a "
                                "draft. Keyboard users expect Enter on a link and Space on a button; a <div> "
                                "pretending to be either responds to neither.",
                                "Link text is read out of context in link lists, so 'Read more' tells nobody "
                                "anything. Write the destination instead.",
                            ],
                            "bullets": [
                                "A clickable <div> needs tabindex, a key handler and a role to be usable — just use the real element",
                                "Give every icon-only button an aria-label",
                                "Never hijack the middle mouse button or Enter on a link",
                            ],
                            "estimated_minutes": 12,
                        },
                        {
                            "title": "A form that people can actually finish",
                            "kind": "code",
                            "summary": "Labels, input types, validation and error messaging.",
                            "paragraphs": [
                                "Every control needs a real <label> wired with for/id. Placeholder text is not a "
                                "label: it disappears the moment you type, and most browsers contrast it too low "
                                "to read comfortably.",
                                "Matching the input type to the data gives you free validation and the right mobile "
                                "keyboard — type='email' and type='tel' are not decorations.",
                            ],
                            "code": {
                                "language": "html",
                                "caption": "An accessible sign-up form",
                                "code": "<form method=\"post\" novalidate>\n  <div class=\"field\">\n    <label for=\"email\">Email</label>\n    <input id=\"email\" name=\"email\" type=\"email\" required\n           autocomplete=\"email\" aria-describedby=\"email-help\" />\n    <p id=\"email-help\" class=\"hint\">We only use this to sign you in.</p>\n  </div>\n\n  <div class=\"field\">\n    <label for=\"password\">Password</label>\n    <input id=\"password\" name=\"password\" type=\"password\" required minlength=\"8\"\n           autocomplete=\"new-password\" />\n  </div>\n\n  <div class=\"field\">\n    <input id=\"terms\" name=\"terms\" type=\"checkbox\" required />\n    <label for=\"terms\">I agree to the community code of conduct</label>\n  </div>\n\n  <button type=\"submit\">Create my account</button>\n</form>",
                            },
                            "note": "The checkbox label comes after the input here, which still works because of the for/id pair — order is purely visual.",
                            "estimated_minutes": 18,
                        },
                        {
                            "title": "Check your understanding",
                            "kind": "quiz",
                            "summary": "Four questions on media, links and forms.",
                            "questions": [
                                {
                                    "prompt": "A decorative divider graphic should be marked with:",
                                    "choices": ["alt=\"divider\"", "no alt attribute at all", "alt=\"\"", "role=\"img\""],
                                    "correct": 2,
                                    "explanation": "An empty alt string keeps it out of the reading order; omitting the attribute makes some readers announce the filename.",
                                },
                                {
                                    "prompt": "Which element performs an action on the current page?",
                                    "choices": ["<a href=\"#\">", "<button>", "<input type=\"text\">", "<span>"],
                                    "correct": 1,
                                    "explanation": "<button> acts; <a> navigates.",
                                },
                                {
                                    "prompt": "Why can a placeholder not replace a <label>?",
                                    "choices": [
                                        "Placeholders are read aloud twice",
                                        "It disappears on input and usually fails contrast requirements",
                                        "Labels are required by HTML validation",
                                        "Placeholders break autocomplete",
                                    ],
                                    "correct": 1,
                                    "explanation": "Once the user types, the hint is gone — so the field has no lasting name.",
                                },
                                {
                                    "prompt": "Setting width and height on an image mainly helps with:",
                                    "choices": [
                                        "SEO ranking",
                                        "Preventing layout shift while the file loads",
                                        "Compressing the image",
                                        "Colour accuracy",
                                    ],
                                    "correct": 1,
                                    "explanation": "The browser reserves the box in advance, so text does not jump.",
                                },
                            ],
                            "estimated_minutes": 6,
                        },
                    ],
                },
            ],
        },
        {
            "title": "Modern CSS: Layout, Tokens and Motion",
            "subtitle": "Flexbox, grid, custom properties and animation — without fighting the browser.",
            "level": "beginner",
            "category": "web",
            "duration_hours": 8,
            "objectives": [
                "Lay out a responsive page with grid and flexbox",
                "Build a design-token system with custom properties",
                "Animate with transform/opacity and respect reduced-motion settings",
            ],
            "requirements": ["Completion of 'Semantic HTML: Pages That Make Sense', or comfortable HTML basics."],
            "modules": [
                {
                    "title": "The box and the cascade",
                    "summary": "Sizing, spacing and how rules actually apply.",
                    "lessons": [
                        {
                            "title": "Box sizing and spacing scales",
                            "kind": "text",
                            "summary": "Stop guessing pixel values.",
                            "paragraphs": [
                                "By default, padding and border are added on top of width, so a 100%-wide element "
                                "with padding overflows. One global rule fixes it: box-sizing: border-box makes "
                                "width describe the whole box, which is what you always assumed it did.",
                                "For spacing, resist arbitrary values. Pick a small scale — 4px as the base, then "
                                "8, 12, 16, 24, 32, 48 — and expose it as custom properties. Layouts built on a "
                                "scale look consistent even when nobody agreed on a design system.",
                            ],
                            "code": {
                                "language": "css",
                                "caption": "A spacing token system",
                                "code": ":root {\n  --sp-1: 4px;\n  --sp-2: 8px;\n  --sp-3: 16px;\n  --sp-4: 24px;\n  --sp-5: 40px;\n}\n\n*,\n*::before,\n*::after {\n  box-sizing: border-box;\n}\n\n.card {\n  padding: var(--sp-4);\n  display: flex;\n  flex-direction: column;\n  gap: var(--sp-2);\n}",
                            },
                            "estimated_minutes": 14,
                        },
                        {
                            "title": "Specificity without a war",
                            "kind": "text",
                            "summary": "Why your rule lost, and how to avoid the fight.",
                            "paragraphs": [
                                "Specificity is counted, not compared: inline styles beat ids, ids beat classes, "
                                "classes beat elements. A selector like .nav > ul li a.active is more specific than "
                                "a single class, which is why one-off overrides spiral.",
                                "The sustainable answer is flat specificity: one class per component, no ids for "
                                "styling, and order your stylesheet so utilities come last. Where you genuinely "
                                "need a boundary, use CSS layers instead of escalating selectors.",
                            ],
                            "note": "If you are reaching for !important, the cascade is telling you the structure is wrong.",
                            "estimated_minutes": 10,
                        },
                    ],
                },
                {
                    "title": "Layout systems",
                    "summary": "Grid for the page, flexbox for the row.",
                    "lessons": [
                        {
                            "title": "Responsive grids with auto-fit",
                            "kind": "code",
                            "summary": "One rule that replaces most media queries.",
                            "paragraphs": [
                                "repeat(auto-fit, minmax(260px, 1fr)) asks the browser to fit as many columns as it "
                                "can, each at least 260px, and stretch them to fill the row. Resize the window and "
                                "the card count changes without a single breakpoint.",
                                "Add grid-template-areas for the page shell — header, sidebar, main, footer — so the "
                                "reading order stays correct on small screens even when the visual order changes.",
                            ],
                            "code": {
                                "language": "css",
                                "caption": "Card grid plus a page shell",
                                "code": ".card-grid {\n  display: grid;\n  gap: var(--sp-3);\n  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));\n}\n\n.shell {\n  display: grid;\n  gap: var(--sp-3);\n  grid-template-areas:\n    \"header header\"\n    \"nav    main\"\n    \"footer footer\";\n  grid-template-columns: 220px 1fr;\n}\n\n@media (max-width: 720px) {\n  .shell {\n    grid-template-areas: \"header\" \"main\" \"nav\" \"footer\";\n    grid-template-columns: 1fr;\n  }\n}",
                            },
                            "estimated_minutes": 16,
                        },
                        {
                            "title": "Flexbox for the small stuff",
                            "kind": "text",
                            "summary": "Alignment, wrapping and the two properties people forget.",
                            "paragraphs": [
                                "Flexbox distributes space along one axis. justify-content moves items along the "
                                "main axis, align-items across the cross axis — mixing those up is the most common "
                                "source of 'why is it not centring'.",
                                "min-width: 0 on a flex child is the fix for overflowing text. Flex items refuse to "
                                "shrink below their content size by default, which is why a long filename pushes the "
                                "whole row off the screen. gap has quietly replaced margin hacks for spacing children.",
                            ],
                            "bullets": [
                                "flex: 1 means grow, shrink and basis 0 — good for equal columns",
                                "flex-wrap: wrap plus gap beats any float grid",
                                "Add min-width: 0 to the child that holds truncated text",
                            ],
                            "estimated_minutes": 12,
                        },
                        {
                            "title": "Motion that respects the reader",
                            "kind": "code",
                            "summary": "Animate transform and opacity, and offer an off switch.",
                            "paragraphs": [
                                "Animating width, top or margin forces the browser to recalculate layout on every "
                                "frame. transform and opacity are composited, so they stay smooth even on a cheap "
                                "phone. Keep durations under 300ms for interface feedback and reserve longer ones "
                                "for genuine storytelling.",
                                "Some people get physically ill from large motion. A prefers-reduced-motion query is "
                                "not a nice-to-have; it is the difference between a usable site and a hostile one.",
                            ],
                            "code": {
                                "language": "css",
                                "caption": "A card reveal with a reduced-motion escape hatch",
                                "code": "@keyframes rise {\n  from { opacity: 0; transform: translateY(12px); }\n  to   { opacity: 1; transform: none; }\n}\n\n.card {\n  animation: rise 240ms ease-out both;\n}\n\n@media (prefers-reduced-motion: reduce) {\n  .card {\n    animation: none;\n  }\n\n  *,\n  *::before,\n  *::after {\n    animation-duration: 1ms !important;\n    transition-duration: 1ms !important;\n  }\n}",
                            },
                            "estimated_minutes": 14,
                        },
                        {
                            "title": "Check your understanding",
                            "kind": "quiz",
                            "summary": "Five questions on tokens, layout and motion.",
                            "questions": [
                                {
                                    "prompt": "Which pair of properties animates without triggering layout recalculation?",
                                    "choices": ["width and height", "transform and opacity", "margin and padding", "top and left"],
                                    "correct": 1,
                                    "explanation": "Both are handled by the compositor rather than the layout engine.",
                                },
                                {
                                    "prompt": "box-sizing: border-box changes which behaviour?",
                                    "choices": [
                                        "Padding and border are counted inside the declared width",
                                        "Margins collapse",
                                        "Elements stack vertically",
                                        "Borders render behind the background",
                                    ],
                                    "correct": 0,
                                    "explanation": "The declared width becomes the total box width.",
                                },
                                {
                                    "prompt": "A flex child with long text pushes its row off screen. The usual fix is:",
                                    "choices": ["overflow: hidden on the parent", "min-width: 0 on the child", "flex-direction: column", "position: absolute"],
                                    "correct": 1,
                                    "explanation": "Flex items default to min-width: auto, so they refuse to shrink below content size.",
                                },
                                {
                                    "prompt": "What does repeat(auto-fit, minmax(260px, 1fr)) do?",
                                    "choices": [
                                        "Creates exactly 260 columns",
                                        "Fits as many tracks as possible, each at least 260px, stretched to fill",
                                        "Locks the grid to one column under 260px",
                                        "Repeats the row 260 times",
                                    ],
                                    "correct": 1,
                                    "explanation": "That single declaration replaces most of the media queries for a card grid.",
                                },
                                {
                                    "prompt": "prefers-reduced-motion is important mainly because:",
                                    "choices": [
                                        "It improves SEO",
                                        "Large motion can trigger nausea and vestibular disorders",
                                        "It reduces CSS file size",
                                        "Animations are otherwise invalid CSS",
                                    ],
                                    "correct": 1,
                                    "explanation": "Honouring the setting is an accessibility requirement, not a stylistic option.",
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

JAVASCRIPT = {
    "title": "JavaScript for Beginners",
    "slug": "javascript-for-beginners",
    "level": "beginner",
    "color": "#fbbf24",
    "icon": "Braces",
    "description": "The language of the browser, from variables to async, taught by reading real code and "
    "predicting what it prints before you run it.",
    "courses": [
        {
            "title": "JavaScript Foundations",
            "subtitle": "Values, control flow and functions — the parts you use every single day.",
            "level": "beginner",
            "category": "javascript",
            "duration_hours": 10,
            "objectives": [
                "Choose between const, let and never-var",
                "Use arrays and objects fluently with map, filter and reduce",
                "Write small functions and reason about scope",
            ],
            "requirements": ["Comfortable with HTML structure."],
            "modules": [
                {
                    "title": "Values and control flow",
                    "summary": "Types, truthiness, and branching that does not surprise you.",
                    "lessons": [
                        {
                            "title": "Variables, types and the three falsy traps",
                            "kind": "text",
                            "summary": "JavaScript has fewer types than you think, and one or two that bite.",
                            "paragraphs": [
                                "Declare with const by default and let only when you know the value will be "
                                "reassigned. var is function-scoped rather than block-scoped and hoists, which "
                                "creates bugs you would rather never meet.",
                                "Primitives are string, number, boolean, null, undefined, symbol and bigint. "
                                "'typeof null' returning 'object' is a famous bug from the first week of the "
                                "language; nothing you can do about it, so remember it. Objects and arrays are "
                                "references: assignment copies the pointer, not the data.",
                            ],
                            "bullets": [
                                "Falsy values are exactly: false, 0, -0, 0n, '', null, undefined, NaN",
                                "Everything else — including [] and {} — is truthy",
                                "NaN === NaN is false; use Number.isNaN(value)",
                                "Prefer === so no coercion happens at all",
                            ],
                            "code": {
                                "language": "javascript",
                                "caption": "Reference behaviour is the usual surprise",
                                "code": "const a = { count: 1 };\nconst b = a;      // same object, not a copy\nb.count = 99;\nconsole.log(a.count); // 99\n\nconst c = [1, 2, 3];\nconst d = [...c];   // a real shallow copy\nd.push(4);\nconsole.log(c.length); // 3",
                            },
                            "estimated_minutes": 15,
                        },
                        {
                            "title": "Conditionals and the nullish operator",
                            "kind": "text",
                            "summary": "Branch clearly, and stop checking for undefined three ways.",
                            "paragraphs": [
                                "'value || fallback' also replaces 0, '' and false — which is usually a bug when "
                                "the value can legitimately be zero. '??' only falls back for null or undefined, "
                                "which is almost always what you meant.",
                                "Guard clauses that return early beat nested ifs. Four levels of indentation is a "
                                "signal that the function should be split.",
                            ],
                            "code": {
                                "language": "javascript",
                                "caption": "Choosing the right fallback operator",
                                "code": "function streak(days) {\n  const goal = days?.goal ?? 7;   // 0 is kept, null/undefined becomes 7\n  if (goal === 0) return 'no goal set';\n  return days.count >= goal ? 'target met' : `${goal - days.count} to go`;\n}",
                            },
                            "estimated_minutes": 12,
                        },
                        {
                            "title": "Workshop: predict the output",
                            "kind": "code",
                            "summary": "Read the snippet, write down what you expect, then run it.",
                            "paragraphs": [
                                "Prediction is the fastest way to find a wrong mental model. Every line below has a "
                                "reason; if any output surprises you, that is exactly the gap to study.",
                            ],
                            "code": {
                                "language": "javascript",
                                "caption": "Predict, then run",
                                "code": "console.log(1 + '2');            // '12'  (string concat wins)\nconsole.log('7' - 3);            // 4     (minus is numeric only)\nconsole.log([] + []);            // ''    (both stringify to '')\nconsole.log(typeof NaN);         // 'number'\nconsole.log(null ?? 'fallback'); // 'fallback'\nconsole.log(0 || 'fallback');    // 'fallback'  <- this one is the trap\nconsole.log(0 ?? 'fallback');    // 0",
                            },
                            "estimated_minutes": 14,
                        },
                    ],
                },
                {
                    "title": "Working with collections",
                    "summary": "map / filter / reduce and object destructuring.",
                    "lessons": [
                        {
                            "title": "map, filter, find and reduce",
                            "kind": "code",
                            "summary": "Four array methods cover most of the everyday work.",
                            "paragraphs": [
                                "map transforms each item and returns a new array of the same length. filter keeps "
                                "items where the callback is truthy. find returns the first match, or undefined. "
                                "reduce folds the array into one value — a total, a grouped object, a maximum.",
                                "None of them mutate the original, which is the point: chained transforms are easy "
                                "to read and easy to test.",
                            ],
                            "code": {
                                "language": "javascript",
                                "caption": "A leaderboard computed from raw rows",
                                "code": "const learners = [\n  { name: 'Ada', xp: 320, streak: 12 },\n  { name: 'Grace', xp: 510, streak: 4 },\n  { name: 'Amina', xp: 275, streak: 21 },\n];\n\nconst onFire = learners\n  .filter((learner) => learner.streak >= 7)\n  .map((learner) => ({ ...learner, label: `${learner.name}: ${learner.xp} XP` }))\n  .sort((a, b) => b.xp - a.xp);\n\nconst totalXp = learners.reduce((sum, learner) => sum + learner.xp, 0);\nconsole.log(onFire.map((row) => row.label));\nconsole.log(totalXp); // 1105",
                            },
                            "note": "sort mutates in place — copy with [...list].sort(...) when you need the original untouched.",
                            "estimated_minutes": 18,
                        },
                        {
                            "title": "Objects, destructuring and spread",
                            "kind": "text",
                            "summary": "Shape data the way functions consume it.",
                            "paragraphs": [
                                "Destructuring pulls named values out of an object, and a default in the pattern "
                                "handles the missing-key case in one place. Because it reads left to right, "
                                "{ streak = 0 } catches undefined but not null.",
                                "Spread builds new objects from old ones without mutation — the pattern every state "
                                "library depends on: { ...user, profile: { ...user.profile, bio } }.",
                            ],
                            "code": {
                                "language": "javascript",
                                "caption": "Destructuring with defaults and renaming",
                                "code": "function greeting({ name, streak = 0, title: role = 'learner' }) {\n  if (streak > 0) return `${name}, ${streak}-day streak as a ${role}`;\n  return `Welcome, ${name}`;\n}\n\ngreeting({ name: 'Ada', title: 'mentor' }); // 'Ada, 0-day streak as a mentor'",
                            },
                            "estimated_minutes": 12,
                        },
                        {
                            "title": "Check your understanding",
                            "kind": "quiz",
                            "summary": "Five questions on foundations.",
                            "questions": [
                                {
                                    "prompt": "Which value is truthy in JavaScript?",
                                    "choices": ["0", "''", "[]", "NaN"],
                                    "correct": 2,
                                    "explanation": "An empty array is an object, and every object is truthy.",
                                },
                                {
                                    "prompt": "What does user?.score ?? 0 do when score is 0?",
                                    "choices": ["Returns 0 from the fallback", "Returns 0 — it is the real value", "Throws", "Returns undefined"],
                                    "correct": 1,
                                    "explanation": "?? only falls back for null or undefined, so a legitimate 0 survives.",
                                },
                                {
                                    "prompt": "Which method returns a single accumulated value?",
                                    "choices": ["map", "filter", "reduce", "forEach"],
                                    "correct": 2,
                                    "explanation": "reduce folds the array into one result via an accumulator.",
                                },
                                {
                                    "prompt": "const b = a where a is an object gives you:",
                                    "choices": ["a deep copy", "a shallow copy", "another reference to the same object", "an error"],
                                    "correct": 2,
                                    "explanation": "Objects are references; use structuredClone(a) for a deep copy.",
                                },
                                {
                                    "prompt": "Why is const preferred over var?",
                                    "choices": [
                                        "It is faster",
                                        "It is block-scoped and cannot be reassigned",
                                        "var is deprecated in ES2015",
                                        "const creates a copy of the object",
                                    ],
                                    "correct": 1,
                                    "explanation": "Block scope plus no reassignment removes two whole classes of bug.",
                                },
                            ],
                            "estimated_minutes": 8,
                        },
                    ],
                },
            ],
        },
        {
            "title": "JavaScript in the Browser",
            "subtitle": "The DOM, events and asynchronous requests against a real API.",
            "level": "beginner",
            "category": "javascript",
            "duration_hours": 9,
            "objectives": [
                "Read and update the DOM without leaking listeners",
                "Handle events, delegation and the default-action trap",
                "Fetch JSON, await it, and render loading, error and empty states",
            ],
            "requirements": ["'JavaScript Foundations' or an equivalent grasp of arrays and functions."],
            "modules": [
                {
                    "title": "DOM and events",
                    "summary": "Selecting, changing and responding.",
                    "lessons": [
                        {
                            "title": "Selecting and changing the page",
                            "kind": "code",
                            "summary": "querySelector plus the properties worth knowing.",
                            "paragraphs": [
                                "querySelector returns the first match or null; querySelectorAll returns a static "
                                "NodeList that becomes an array with [...]. Cache references when you will touch the "
                                "same node repeatedly — the DOM is slow compared with plain object access.",
                                "Prefer classList.toggle over string surgery on className, and textContent over "
                                "innerHTML whenever the content is plain text. innerHTML on user input is an XSS "
                                "vulnerability, not a style choice.",
                            ],
                            "code": {
                                "language": "javascript",
                                "caption": "Safe DOM updates",
                                "code": "const list = document.querySelector('#feed');\nconst card = document.createElement('li');\n\ncard.className = 'post';\ncard.textContent = post.title;         // safe: never parses HTML\ncard.dataset.id = String(post.id);\n\nlist.append(card);\nlist.classList.toggle('is-empty', list.children.length === 0);",
                            },
                            "estimated_minutes": 15,
                        },
                        {
                            "title": "Events, bubbling and delegation",
                            "kind": "text",
                            "summary": "One listener instead of one hundred.",
                            "paragraphs": [
                                "Click events bubble from the target up through every ancestor. Delegation puts a "
                                "single listener on the container and reads event.target.closest('.like-button'), so "
                                "rows added later are handled automatically and you never forget to unsubscribe.",
                                "Some default actions are what you want to stop — form submission reloading the page "
                                "— so call event.preventDefault(). Stopping propagation is rarely needed; use it only "
                                "when an ancestor genuinely must not see the event.",
                            ],
                            "code": {
                                "language": "javascript",
                                "caption": "Delegated clicks on a dynamic list",
                                "code": "document.querySelector('#feed').addEventListener('click', (event) => {\n  const button = event.target.closest('[data-action]');\n  if (!button) return;\n\n  if (button.dataset.action === 'like') {\n    event.preventDefault();\n    toggleLike(button.closest('.post').dataset.id);\n  }\n});",
                            },
                            "note": "Always remove listeners you added outside delegation — addEventListener in a component that mounts repeatedly is a leak.",
                            "estimated_minutes": 14,
                        },
                    ],
                },
                {
                    "title": "Asynchronous JavaScript",
                    "summary": "Promises, async/await, and talking to the CodeHer API.",
                    "lessons": [
                        {
                            "title": "Promises and async/await",
                            "kind": "code",
                            "summary": "One pending state, three outcomes.",
                            "paragraphs": [
                                "A promise is a value that has not arrived yet. It settles once: fulfilled or "
                                "rejected. async functions return a promise, and await pauses that function until "
                                "it settles, letting you write ordinary-looking code for asynchronous work.",
                                "Wrap await in try/catch for the rejection path, and put anything that must happen "
                                "either way in finally — clearing a loading flag is the classic case. Never fire two "
                                "independent awaits in sequence when Promise.all can run them together.",
                            ],
                            "code": {
                                "language": "javascript",
                                "caption": "Fetching a course and its curriculum in parallel",
                                "code": "async function loadCourse(slug) {\n  const [courseResponse, curriculumResponse] = await Promise.all([\n    fetch(`/api/learning/courses/${slug}/`),\n    fetch(`/api/learning/courses/${slug}/curriculum/`),\n  ]);\n\n  if (!courseResponse.ok || !curriculumResponse.ok) {\n    throw new Error(`Request failed: ${courseResponse.status}`);\n  }\n\n  return {\n    course: await courseResponse.json(),\n    curriculum: await curriculumResponse.json(),\n  };\n}\n\ntry {\n  const data = await loadCourse('javascript-foundations');\n  render(data);\n} catch (error) {\n  showError(error.message);\n} finally {\n  setLoading(false);\n}",
                            },
                            "estimated_minutes": 18,
                        },
                        {
                            "title": "Check your understanding",
                            "kind": "quiz",
                            "summary": "Four questions on the browser side.",
                            "questions": [
                                {
                                    "prompt": "Which is safe when inserting a user's display name?",
                                    "choices": ["element.innerHTML = name", "element.textContent = name", "element.insertAdjacentHTML('beforeend', name)", "eval(name)"],
                                    "correct": 1,
                                    "explanation": "textContent treats the input as text, so markup cannot execute.",
                                },
                                {
                                    "prompt": "Event delegation works because events do what after firing?",
                                    "choices": ["Bubble up through ancestors", "Reset the page", "Queue in the microtask list", "Clone to the document"],
                                    "correct": 0,
                                    "explanation": "The container sees events from children added later, with one listener.",
                                },
                                {
                                    "prompt": "What does await do if the promise rejects and there is no try/catch?",
                                    "choices": ["Returns undefined", "Rejects the enclosing async function's promise", "Retries the call", "Blocks the event loop"],
                                    "correct": 1,
                                    "explanation": "The rejection propagates to whoever called the async function.",
                                },
                                {
                                    "prompt": "Two independent requests should be started with:",
                                    "choices": ["Sequential awaits", "Promise.all", "setTimeout", "A while loop"],
                                    "correct": 1,
                                    "explanation": "Promise.all runs them concurrently and waits for both.",
                                },
                            ],
                            "estimated_minutes": 7,
                        },
                    ],
                },
            ],
        },
    ],
}
