import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { motion, useReducedMotion } from "framer-motion";
import CodeMirror, { EditorView } from "@uiw/react-codemirror";
import { javascript } from "@codemirror/lang-javascript";
import { python as pythonLang } from "@codemirror/lang-python";
import { oneDark } from "@codemirror/theme-one-dark";
import {
  ArrowLeft,
  CircleCheck,
  CircleX,
  Clock,
  Code2,
  Info,
  Lightbulb,
  ListChecks,
  Loader2,
  Lock,
  Play,
  RotateCcw,
  Save,
  Send,
  Sparkles,
  Timer,
  Trophy,
  X,
  Zap,
} from "lucide-react";
import { api, endpoints } from "../../services/api";
import { useAsync, useDebouncedValue } from "../../hooks";
import {
  Alert,
  Badge,
  Button,
  Card,
  Chip,
  ChipRow,
  ConfirmDialog,
  EmptyState,
  ErrorState,
  LevelBadge,
  ProgressBar,
  Select,
  Skeleton,
  SkeletonText,
} from "../../components/ui";
import { useAuth } from "../../context/AuthContext";
import { useToast } from "../../context/ToastContext";
import "./challenges.css";

const LANGUAGES = {
  javascript: { label: "JavaScript", extension: () => javascript(), file: "solution.js" },
  python: { label: "Python", extension: () => pythonLang(), file: "solution.py" },
};

const draftKey = (id, language) => `codeher.challenge.${id}.${language}.draft`;

/** Runner payloads mix primitives and objects — render anything as readable text. */
function valueText(value) {
  if (value === null || value === undefined) return "";
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

function pick(source, keys) {
  for (const key of keys) {
    const value = source?.[key];
    if (value !== undefined && value !== null && value !== "") return value;
  }
  return undefined;
}

/** Ratios arrive as either 0.42 or 42 depending on the serializer — normalise to a percentage. */
function toPercent(...values) {
  for (const value of values) {
    if (value === null || value === undefined || value === "") continue;
    const parsed = Number(value);
    if (!Number.isNaN(parsed)) return Math.round(parsed <= 1 ? parsed * 100 : parsed);
  }
  return null;
}

function asList(value) {
  if (Array.isArray(value)) return value.map((item) => String(item)).filter(Boolean);
  if (typeof value === "string" && value.trim()) {
    return value
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);
  }
  return [];
}

function formatDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

function ms(value) {
  if (value === null || value === undefined) return "—";
  const parsed = Number(value);
  return Number.isNaN(parsed) ? String(value) : `${parsed.toLocaleString()} ms`;
}

/** Honest failure copy: a rejected run is reported, never dressed up as a pass. */
function describeError(error, fallback) {
  if (!error) return fallback;
  if (error.status === 401) return "Your session expired. Sign in again to run or submit code.";
  if (error.status === 403) return error.detail || "You do not have permission to run this challenge.";
  if (error.status === 404) return error.detail || "This challenge no longer exists.";
  if (error.status === 429) return error.detail || "The sandbox is busy — wait a moment and try again.";
  const field = error.fieldErrors?.code ?? error.fieldErrors?.language;
  if (field?.length) return field.join(" ");
  return error.detail || error.message || fallback;
}

function readStarterMap(detail) {
  const raw = detail?.starter_code ?? detail?.starterCode;
  const map = {};
  if (raw && typeof raw === "object") {
    if (typeof raw.javascript === "string") map.javascript = raw.javascript;
    else if (typeof raw.js === "string") map.javascript = raw.js;
    if (typeof raw.python === "string") map.python = raw.python;
    else if (typeof raw.py === "string") map.python = raw.py;
  }
  const languages = Object.keys(map);
  return { map, languages: languages.length ? languages : Object.keys(LANGUAGES) };
}

function readExamples(detail) {
  const raw = detail?.examples ?? detail?.worked_examples ?? [];
  const list = Array.isArray(raw) ? raw : typeof raw === "string" ? raw.split(/\n{2,}/) : [];
  return list
    .map((item, index) => {
      if (typeof item === "string") return { id: index, text: item };
      return {
        id: index,
        title: pick(item, ["name", "title", "label"]) ?? `Example ${index + 1}`,
        input: valueText(pick(item, ["input", "args", "call", "given", "example_input"])),
        expected: valueText(
          pick(item, ["expected", "expected_output", "output", "result", "returns"])
        ),
        explanation: valueText(
          pick(item, ["explanation", "note", "why", "description", "walkthrough"])
        ),
      };
    })
    .filter((item) => item.text || item.input || item.expected || item.explanation);
}

/** Only publicly documented cases reach the DOM — anything flagged hidden stays server-side. */
function readSamples(detail) {
  const raw = pick(detail, ["sample_tests", "public_tests", "visible_tests", "test_cases", "tests"]);
  const list = Array.isArray(raw) ? raw : [];
  return list
    .filter(
      (item) => item && item.hidden !== true && item.is_hidden !== true && item.is_public !== false
    )
    .map((item, index) => ({
      id: item?.id ?? index,
      name: pick(item, ["name", "title", "description"]) ?? `Sample test ${index + 1}`,
      input: valueText(pick(item, ["input", "args", "arguments", "call", "given"])),
      expected: valueText(pick(item, ["expected", "expected_output", "output", "want", "result"])),
    }));
}

/** `/challenges/{id}/submissions/me/` is documented as "best + recent" — flatten either envelope. */
function readSubmissions(payload) {
  const buckets = [];
  if (Array.isArray(payload)) buckets.push(...payload);
  else if (payload) {
    if (Array.isArray(payload.results)) buckets.push(...payload.results);
    if (Array.isArray(payload.recent)) buckets.push(...payload.recent);
    if (Array.isArray(payload.submissions)) buckets.push(...payload.submissions);
    if (payload.best && typeof payload.best === "object") buckets.push(payload.best);
  }

  const seen = new Set();
  const unique = buckets.filter((item) => {
    if (!item) return false;
    const key = item.id ?? JSON.stringify(item);
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });

  return unique.sort(
    (a, b) => new Date(b.created_at ?? 0).getTime() - new Date(a.created_at ?? 0).getTime()
  );
}

const CELEBRATION_COLORS = ["#8b5cf6", "#ec4899", "#22d3ee", "#34d399", "#fbbf24"];

function Celebration({ onDone }) {
  const reduce = useReducedMotion();
  const pieces = useMemo(
    () =>
      Array.from({ length: 32 }, (_, index) => ({
        id: index,
        left: (index * 31) % 100,
        color: CELEBRATION_COLORS[index % CELEBRATION_COLORS.length],
        delay: (index % 8) * 0.07,
        drift: ((index % 7) - 3) * 14,
        spin: 200 + (index % 5) * 120,
      })),
    []
  );

  useEffect(() => {
    const timer = setTimeout(onDone, 2400);
    return () => clearTimeout(timer);
  }, [onDone]);

  if (reduce) return null;

  return (
    <div className="celebrate" aria-hidden="true">
      {pieces.map((piece) => (
        <motion.span
          key={piece.id}
          className="celebrate__piece"
          style={{ left: `${piece.left}%`, background: piece.color }}
          initial={{ y: -30, opacity: 0, rotate: 0 }}
          animate={{ y: 640, x: piece.drift, rotate: piece.spin, opacity: [0, 1, 1, 0] }}
          transition={{ duration: 1.7, delay: piece.delay, ease: "easeIn" }}
        />
      ))}
    </div>
  );
}

function RunResult({ result }) {
  const results = Array.isArray(result?.results) ? result.results : [];
  const passed = results.filter((item) => item.passed === true).length;
  const allPassed = results.length > 0 && passed === results.length;

  return (
    <Card as="section" className="results">
      <div className="run-flag">
        <Info size={15} aria-hidden="true" />
        <span>
          Run executes the sample cases only. It awards no points, grants no XP and does not appear
          in your submission history — only Submit is scored.
        </span>
      </div>

      <div className="results__head">
        <span className={`verdict ${allPassed ? "verdict--pass" : "verdict--fail"}`}>
          {allPassed ? <CircleCheck size={17} /> : <CircleX size={17} />}
          {results.length === 0
            ? "No sample results returned"
            : `${passed} of ${results.length} sample tests passed`}
        </span>
        <span className="muted num" style={{ fontSize: "var(--fs-xs)" }}>
          <Timer size={13} style={{ verticalAlign: -2 }} /> {ms(result?.runtime_ms)}
        </span>
      </div>

      {results.length === 0 ? (
        <p className="muted" style={{ fontSize: "var(--fs-sm)" }}>
          The sandbox executed your code but returned no per-test results. Check that the function
          name and signature match the brief, then run again.
        </p>
      ) : (
        <ul className="test-list">
          {results.map((item, index) => (
            <li
              key={`${item.name ?? "case"}-${index}`}
              className={`test-row ${item.passed ? "test-row--pass" : "test-row--fail"}`.trim()}
            >
              <span className="test-row__name">
                <span className="test-row__icon">
                  {item.passed ? <CircleCheck size={16} /> : <CircleX size={16} />}
                </span>
                {item.name ?? `Test ${index + 1}`}
                <Badge variant={item.passed ? "success" : "danger"}>
                  {item.passed ? "Pass" : "Fail"}
                </Badge>
              </span>
              <span className="test-row__body">
                <span className="kv">
                  <span className="kv__label">Expected</span>
                  <code className="kv__value">{valueText(item.expected) || "—"}</code>
                </span>
                <span className="kv">
                  <span className="kv__label">Your output</span>
                  <code className="kv__value">{valueText(item.actual) || "—"}</code>
                </span>
              </span>
              {item.error && <code className="test-row__error">{valueText(item.error)}</code>}
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}

export default function ChallengeWorkspace() {
  const { id } = useParams();
  const { isAuthenticated, isBooting } = useAuth();
  const toast = useToast();
  const reduce = useReducedMotion();

  const detail = useAsync((signal) => api.get(`${endpoints.challenges}${id}/`, { signal }), [id]);
  const history = useAsync(
    (signal) => api.get(`${endpoints.challenges}${id}/submissions/me/`, { signal }),
    [id],
    { skip: !isAuthenticated }
  );

  const starter = useMemo(() => readStarterMap(detail.data), [detail.data]);
  const examples = useMemo(() => readExamples(detail.data), [detail.data]);
  const samples = useMemo(() => readSamples(detail.data), [detail.data]);
  const submissions = useMemo(() => readSubmissions(history.data), [history.data]);

  const [language, setLanguage] = useState("javascript");
  const [code, setCode] = useState("");
  const [restoredFrom, setRestoredFrom] = useState(null);
  const [draftSaved, setDraftSaved] = useState(true);
  const [confirmReset, setConfirmReset] = useState(false);
  const [runResult, setRunResult] = useState(null);
  const [runError, setRunError] = useState(null);
  const [running, setRunning] = useState(false);
  const [submission, setSubmission] = useState(null);
  const [submitError, setSubmitError] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [celebrate, setCelebrate] = useState(false);
  const [solvedNow, setSolvedNow] = useState(false);

  const mounted = useRef(true);
  const inFlight = useRef(false);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  const solvedByBest = useMemo(() => submissions.some((item) => Boolean(item.passed)), [submissions]);
  const solved =
    solvedNow ||
    Boolean(detail.data?.is_solved ?? detail.data?.solved ?? detail.data?.user_has_solved) ||
    solvedByBest;

  /** A saved draft wins over the starter so a refresh cannot lose work. */
  const applyContent = useCallback(
    (lang) => {
      const base = starter.map[lang] ?? "";
      let saved = null;
      try {
        saved = localStorage.getItem(draftKey(id, lang));
      } catch {
        saved = null; // storage blocked (private mode) — fall back to the starter
      }
      if (saved && saved !== base) {
        setCode(saved);
        setRestoredFrom(lang);
      } else {
        setCode(base);
        setRestoredFrom(null);
      }
      setDraftSaved(true);
    },
    [id, starter.map]
  );

  useEffect(() => {
    if (!detail.data) return;
    const initial = starter.languages.includes("javascript") ? "javascript" : starter.languages[0];
    setLanguage(initial);
    applyContent(initial);
    setSolvedNow(false);
    setRunResult(null);
    setRunError(null);
    setSubmission(null);
    setSubmitError(null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [detail.data, id]);

  const debouncedCode = useDebouncedValue(code, 700);
  const isStarterCode = debouncedCode === (starter.map[language] ?? "");

  useEffect(() => {
    if (!detail.data || isStarterCode) return;
    try {
      localStorage.setItem(draftKey(id, language), debouncedCode);
      setDraftSaved(true);
    } catch {
      setDraftSaved(false);
    }
  }, [debouncedCode, id, language, isStarterCode, detail.data]);

  const clearResults = () => {
    setRunResult(null);
    setRunError(null);
    setSubmission(null);
    setSubmitError(null);
  };

  const changeLanguage = (next) => {
    if (!LANGUAGES[next] || next === language) return;
    setLanguage(next);
    applyContent(next);
    clearResults();
  };

  const resetToStarter = () => {
    try {
      localStorage.removeItem(draftKey(id, language));
    } catch {
      /* nothing to clean up when storage is unavailable */
    }
    setCode(starter.map[language] ?? "");
    setRestoredFrom(null);
    setDraftSaved(true);
    setConfirmReset(false);
    clearResults();
    toast.info("Starter code restored for this challenge.");
  };

  const busy = running || submitting;
  const canSend = isAuthenticated && code.trim().length > 0;

  const runCode = async () => {
    if (!canSend || inFlight.current) return;
    inFlight.current = true;
    setRunning(true);
    setRunError(null);
    try {
      const result = await api.post(`${endpoints.challenges}${id}/run/`, { language, code });
      if (!mounted.current) return;
      setSubmission(null);
      setRunResult(result ?? { ok: false, results: [] });
      if (result?.ok === false && !Array.isArray(result?.results)) {
        setRunError(valueText(result?.error) || "The sandbox reported a failure with no test results.");
      }
    } catch (error) {
      if (error?.name === "AbortError" || !mounted.current) return;
      setRunResult(null);
      setRunError(describeError(error, "We could not run your code in the sandbox."));
      toast.error("The run did not complete — nothing was executed or scored.");
    } finally {
      inFlight.current = false;
      if (mounted.current) setRunning(false);
    }
  };

  const submitCode = async () => {
    if (!canSend || inFlight.current) return;
    inFlight.current = true;
    setSubmitting(true);
    setSubmitError(null);
    try {
      const result = await api.post(`${endpoints.challenges}${id}/submit/`, { language, code });
      if (!mounted.current) return;
      setSubmission(result ?? null);
      setRunResult(null);

      const total = Number(result?.total_tests ?? 0);
      const passedCount = Number(result?.passed_count ?? 0);
      const allPassed = result?.passed === true || (total > 0 && passedCount === total);
      const points = Number(result?.points_awarded ?? 0);

      if (allPassed) {
        toast.success(
          result?.first_solve_bonus
            ? `Solved! +${points} points, first-solve bonus included.`
            : points > 0
              ? `All tests passed — +${points} points.`
              : "All tests passed.",
          { title: "Challenge solved" }
        );
        setSolvedNow(true);
        if (!reduce) setCelebrate(true);
      } else {
        toast.warning(
          total > 0
            ? `${passedCount} of ${total} tests passed — no points this time.`
            : "The hidden suite did not fully pass."
        );
      }
      history.reload();
    } catch (error) {
      if (error?.name === "AbortError" || !mounted.current) return;
      setSubmission(null);
      setSubmitError(describeError(error, "Your submission could not be recorded."));
      toast.error("Nothing was recorded — the submission never reached the server.");
    } finally {
      inFlight.current = false;
      if (mounted.current) setSubmitting(false);
    }
  };

  const extensions = useMemo(
    () => [LANGUAGES[language].extension(), EditorView.lineWrapping],
    [language]
  );

  const scorePercent = Number.isNaN(Number(submission?.score))
    ? null
    : toPercent(submission?.score);
  const passRate = toPercent(detail.data?.pass_rate, detail.data?.acceptance_rate);
  const paragraphs = String(detail.data?.description ?? "")
    .split(/\n{2,}/)
    .filter((line) => line.trim());

  if (detail.error && !detail.loading) {
    return (
      <div className="container workspace">
        <Link className="workspace__back" to="/challenges">
          <ArrowLeft size={15} /> Back to challenges
        </Link>
        <h1 className="sr-only">Challenge unavailable</h1>
        <ErrorState
          error={detail.error}
          onRetry={detail.reload}
          title={detail.error.status === 404 ? "Challenge not found" : "We could not load this challenge"}
        />
      </div>
    );
  }

  return (
    <div className="container workspace">
      {celebrate && <Celebration onDone={() => setCelebrate(false)} />}

      <header className="workspace__header">
        <Link className="workspace__back" to="/challenges">
          <ArrowLeft size={15} /> Back to challenges
        </Link>

        {detail.loading ? (
          <>
            <Skeleton className="skeleton--title" style={{ width: "45%" }} />
            <Skeleton style={{ height: 18, width: "70%" }} />
          </>
        ) : (
          <>
            <div className="workspace__title-row">
              <h1>{detail.data?.title ?? "Challenge"}</h1>
              <LevelBadge level={detail.data?.difficulty ?? detail.data?.level} />
              {isAuthenticated && solved && (
                <Badge variant="success">
                  <CircleCheck size={12} /> Solved
                </Badge>
              )}
            </div>
            <div className="workspace__facts">
              <span className="challenge-card__stat challenge-card__stat--points">
                <Zap size={13} /> {detail.data?.points ?? 0} points
              </span>
              {passRate !== null && (
                <span className="challenge-card__stat challenge-card__stat--rate">
                  <Trophy size={13} /> {passRate}% pass rate
                </span>
              )}
              <span className="challenge-card__stat">
                <Code2 size={13} /> {starter.languages.map((key) => LANGUAGES[key].label).join(" · ")}
              </span>
              <ChipRow>
                {asList(detail.data?.categories ?? detail.data?.category).map((tag) => (
                  <Chip key={tag}>{tag}</Chip>
                ))}
              </ChipRow>
            </div>
          </>
        )}
      </header>

      <div className="workspace__panes">
        {/* ---------------- Left pane: the brief ---------------- */}
        <div className="workspace__pane workspace__pane--brief">
          <Card as="section" aria-labelledby="brief-title">
            <div className="brief">
              <h2 id="brief-title">Instructions</h2>
              {detail.loading ? (
                <SkeletonText lines={5} />
              ) : paragraphs.length ? (
                <div className="brief__body">
                  {paragraphs.map((para, index) => (
                    <p key={index}>{para}</p>
                  ))}
                </div>
              ) : (
                <p className="muted" style={{ fontSize: "var(--fs-sm)" }}>
                  No written instructions were saved for this challenge.
                </p>
              )}

              {detail.data?.function_name && (
                <>
                  <h3>Function signature</h3>
                  <div className="signature">
                    <Code2 size={15} aria-hidden="true" />
                    <code>{String(detail.data.function_name)}</code>
                    {detail.data?.function_signature ? (
                      <code>{String(detail.data.function_signature)}</code>
                    ) : null}
                  </div>
                  <p className="ide__hint">
                    Keep this exact name and parameter order — the hidden suite calls it directly.
                  </p>
                </>
              )}
            </div>
          </Card>

          {!detail.loading && examples.length > 0 && (
            <Card as="section" aria-labelledby="examples-title">
              <div className="brief">
                <h2 id="examples-title">
                  <Lightbulb size={16} style={{ verticalAlign: -3 }} /> Worked examples
                </h2>
                <div className="stack" style={{ gap: "var(--sp-3)" }}>
                  {examples.map((example) =>
                    example.text ? (
                      <p
                        key={example.id}
                        style={{ fontSize: "var(--fs-sm)", color: "var(--text-secondary)" }}
                      >
                        {example.text}
                      </p>
                    ) : (
                      <div className="example" key={example.id}>
                        <span className="example__title">{example.title}</span>
                        <div className="kv kv--grid">
                          {Boolean(example.input) && (
                            <span className="kv">
                              <span className="kv__label">Input</span>
                              <code className="kv__value">{example.input}</code>
                            </span>
                          )}
                          {Boolean(example.expected) && (
                            <span className="kv">
                              <span className="kv__label">Expected</span>
                              <code className="kv__value">{example.expected}</code>
                            </span>
                          )}
                        </div>
                        {Boolean(example.explanation) && (
                          <p className="muted" style={{ fontSize: "var(--fs-xs)" }}>
                            {example.explanation}
                          </p>
                        )}
                      </div>
                    )
                  )}
                </div>
              </div>
            </Card>
          )}

          {!detail.loading && (
            <Card as="section" aria-labelledby="samples-title">
              <div className="brief">
                <h2 id="samples-title">
                  <ListChecks size={16} style={{ verticalAlign: -3 }} /> Sample test cases
                </h2>
                {samples.length === 0 ? (
                  <p className="samples__note">
                    <Info size={14} aria-hidden="true" />
                    This challenge publishes no sample cases. Use Run to explore behaviour — the
                    hidden suite executes only when you submit.
                  </p>
                ) : (
                  <>
                    <ul className="samples">
                      {samples.map((sample) => (
                        <li className="samples__item" key={sample.id}>
                          <span className="samples__name">
                            <CircleCheck size={14} style={{ color: "var(--text-muted)" }} aria-hidden="true" />
                            {sample.name}
                          </span>
                          <div className="kv kv--grid">
                            <span className="kv">
                              <span className="kv__label">Input</span>
                              <code className="kv__value">{sample.input || "—"}</code>
                            </span>
                            <span className="kv">
                              <span className="kv__label">Expected output</span>
                              <code className="kv__value">{sample.expected || "—"}</code>
                            </span>
                          </div>
                        </li>
                      ))}
                    </ul>
                    <p className="samples__note">
                      <Lock size={14} aria-hidden="true" />
                      Additional hidden tests run in the sandbox when you submit. They are never
                      listed here.
                    </p>
                  </>
                )}
              </div>
            </Card>
          )}

          <Card as="section" aria-labelledby="history-title">
            <div className="brief">
              <h2 id="history-title">Your submissions</h2>
              {isBooting ? (
                <p className="history__empty">Checking your session…</p>
              ) : !isAuthenticated ? (
                <p className="history__empty">
                  Sign in and every scored attempt is recorded here automatically.
                </p>
              ) : history.loading ? (
                <Skeleton style={{ height: 120 }} />
              ) : history.error ? (
                <ErrorState
                  error={history.error}
                  onRetry={history.reload}
                  title="Your history did not load"
                />
              ) : submissions.length === 0 ? (
                <p className="history__empty">No submissions yet for this challenge.</p>
              ) : (
                <div className="table-wrap">
                  <table className="table">
                    <caption className="sr-only">
                      Your recorded submissions for this challenge, newest first
                    </caption>
                    <thead>
                      <tr>
                        <th scope="col">Language</th>
                        <th scope="col">Tests passed</th>
                        <th scope="col">Points</th>
                        <th scope="col">Runtime</th>
                        <th scope="col">Submitted</th>
                      </tr>
                    </thead>
                    <tbody>
                      {submissions.map((item, index) => {
                        const tone = item.passed
                          ? "pass-ratio--ok"
                          : Number(item.passed_count ?? 0) > 0
                            ? "pass-ratio--partial"
                            : "pass-ratio--none";
                        return (
                          <tr key={item.id ?? `submission-${index}`}>
                            <td>
                              <span className="lang-cell">
                                <Code2 size={14} aria-hidden="true" />
                                {LANGUAGES[item.language]?.label ?? item.language ?? "—"}
                              </span>
                            </td>
                            <td className={`num ${tone}`.trim()}>
                              {Number(item.passed_count ?? 0)} / {Number(item.total_tests ?? 0)}
                              {item.passed ? <span className="sr-only"> — all passed</span> : null}
                            </td>
                            <td className="num">
                              {Number(item.points_awarded ?? 0) > 0
                                ? `+${item.points_awarded}`
                                : "0"}
                            </td>
                            <td className="num muted">{ms(item.runtime_ms)}</td>
                            <td className="muted">{formatDate(item.created_at)}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </Card>
        </div>

        {/* ---------------- Right pane: the editor ---------------- */}
        <div className="workspace__pane workspace__pane--ide">
          <div className="ide">
            <div className="ide__bar">
              <span className="ide__file">
                <Code2 size={14} aria-hidden="true" />
                {LANGUAGES[language].file}
              </span>
              <div className="ide__bar-controls">
                <label className="sr-only" htmlFor="challenge-language">
                  Solution language
                </label>
                <Select
                  id="challenge-language"
                  className="select ide__lang"
                  value={language}
                  onChange={(event) => changeLanguage(event.target.value)}
                  disabled={busy}
                >
                  {starter.languages.map((key) => (
                    <option key={key} value={key}>
                      {LANGUAGES[key].label}
                    </option>
                  ))}
                </Select>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setConfirmReset(true)}
                  disabled={busy || !isAuthenticated}
                >
                  <RotateCcw size={14} /> Reset starter
                </Button>
              </div>
            </div>

            <div className="ide__editor">
              {detail.loading ? (
                <Skeleton style={{ height: "100%", borderRadius: 0 }} />
              ) : (
                <CodeMirror
                  value={code}
                  onChange={(next) => {
                    setCode(next);
                    setDraftSaved(false);
                  }}
                  extensions={extensions}
                  theme={oneDark}
                  height="100%"
                  editable={isAuthenticated}
                  readOnly={!isAuthenticated}
                  indentWithTab
                  aria-label="Challenge solution code editor"
                  basicSetup={{
                    lineNumbers: true,
                    foldGutter: false,
                    autocompletion: true,
                    highlightActiveLine: true,
                    highlightActiveLineGutter: false,
                  }}
                />
              )}
            </div>

            <div className="ide__foot">
              {isBooting ? (
                <span className="ide__hint">
                  <Loader2 size={14} className="spin" /> Checking your session…
                </span>
              ) : !isAuthenticated ? (
                <div className="gate">
                  <span className="ide__hint">
                    The brief and the editor stay readable, but running and scoring need an account.
                  </span>
                  <Button size="sm" to="/signin" state={{ from: `/challenges/${id}` }}>
                    <Lock size={15} /> Sign in to run &amp; submit
                  </Button>
                </div>
              ) : (
                <>
                  <Button
                    variant="outline"
                    onClick={runCode}
                    disabled={busy || !code.trim()}
                    loading={running}
                  >
                    <Play size={15} /> Run sample tests
                  </Button>
                  <Button onClick={submitCode} disabled={busy || !code.trim()} loading={submitting}>
                    <Send size={15} /> Submit for score
                  </Button>
                  <span className="ide__save-state" role="status">
                    {draftSaved ? (
                      <>
                        <Save size={13} /> Draft saved on this device
                      </>
                    ) : (
                      <>
                        <Loader2 size={13} className="spin" /> Saving draft…
                      </>
                    )}
                  </span>
                </>
              )}
            </div>
          </div>

          {!isAuthenticated && !isBooting && (
            <p className="ide__hint">
              The editor is read-only while signed out — sign in to type, run and submit.
            </p>
          )}

          {restoredFrom === language && isAuthenticated && (
            <div className="alert alert--info" role="status">
              <Info size={16} aria-hidden="true" />
              <span style={{ flex: 1 }}>
                Draft restored for {LANGUAGES[language].label} — this is your own unsaved work from
                this device, not the starter code.
              </span>
              <button type="button" onClick={() => setRestoredFrom(null)} aria-label="Dismiss draft notice">
                <X size={15} />
              </button>
            </div>
          )}

          <section className="results-stack" aria-label="Run results" aria-live="polite">
            {running && (
              <p className="ide__hint">
                <Loader2 size={14} className="spin" /> Running your code in the sandbox…
              </p>
            )}
            {runError && (
              <Alert variant="error" title="The run did not succeed" onDismiss={() => setRunError(null)}>
                {runError}
              </Alert>
            )}
            {runResult && !runError && <RunResult result={runResult} />}
          </section>

          <section className="results-stack" aria-label="Submission result" aria-live="polite">
            {submitError && (
              <Alert
                variant="error"
                title="Submission not recorded"
                onDismiss={() => setSubmitError(null)}
              >
                {submitError}
              </Alert>
            )}

            {submission && (
              <Card as="section" className="results">
                <div className="results__head">
                  <span className={`verdict ${submission.passed ? "verdict--pass" : "verdict--fail"}`}>
                    {submission.passed ? <CircleCheck size={18} /> : <CircleX size={18} />}
                    {submission.passed ? "All tests passed" : "Not solved yet"}
                  </span>
                  <span className="muted num" style={{ fontSize: "var(--fs-xs)" }}>
                    <Clock size={13} style={{ verticalAlign: -2 }} /> {ms(submission.runtime_ms)}
                  </span>
                </div>

                {scorePercent !== null && (
                  <ProgressBar
                    value={scorePercent}
                    showValue
                    thin
                    variant={submission.passed ? "success" : undefined}
                    label="Test score"
                  />
                )}

                <div className="award">
                  <span className="award__points">
                    {Number(submission.passed_count ?? 0)} / {Number(submission.total_tests ?? 0)} tests
                  </span>
                  <span className="row" style={{ gap: "var(--sp-2)" }}>
                    <Badge
                      variant={Number(submission.points_awarded ?? 0) > 0 ? "brand" : "neutral"}
                    >
                      <Zap size={12} /> {Number(submission.points_awarded ?? 0)} points awarded
                    </Badge>
                    {submission.first_solve_bonus && (
                      <span className="bonus-flag">
                        <Sparkles size={13} /> First-solve bonus
                      </span>
                    )}
                  </span>
                </div>

                {typeof submission.error === "string" && submission.error && (
                  <Alert variant="warning" title="Message from the sandbox">
                    <code style={{ fontFamily: "var(--font-mono)", fontSize: "var(--fs-xs)" }}>
                      {submission.error}
                    </code>
                  </Alert>
                )}

                <p className="ide__hint">
                  {submission.passed
                    ? `Recorded as submission #${submission.id ?? "—"} and shown in your history.`
                    : "This attempt is stored in your history, but awarded no points because the suite did not fully pass."}
                </p>

                {!submission.passed && (
                  <Button variant="ghost" size="sm" onClick={submitCode} disabled={busy}>
                    <RotateCcw size={14} /> Submit again
                  </Button>
                )}
              </Card>
            )}

            {!submission && !submitError && !submitting && (
              <EmptyState
                icon={Trophy}
                title={
                  isAuthenticated
                    ? "Nothing submitted yet"
                    : "Reading mode: sign in to get scored"
                }
                description="Run checks the sample cases for free. Submit runs the hidden suite, records the attempt and awards points."
                action={
                  isAuthenticated ? (
                    <Button variant="ghost" size="sm" onClick={runCode} disabled={busy || !code.trim()}>
                      <Play size={14} /> Run the sample tests
                    </Button>
                  ) : (
                    <Button size="sm" variant="outline" to="/signin" state={{ from: `/challenges/${id}` }}>
                      Sign in
                    </Button>
                  )
                }
              />
            )}
          </section>
        </div>
      </div>

      <ConfirmDialog
        open={confirmReset}
        onClose={() => setConfirmReset(false)}
        onConfirm={resetToStarter}
        title="Discard your current code?"
        message="Resetting restores the starter code for this language and deletes the draft saved on this device. Recorded submissions are not affected."
        confirmLabel="Reset to starter code"
        variant="danger"
      />
    </div>
  );
}
