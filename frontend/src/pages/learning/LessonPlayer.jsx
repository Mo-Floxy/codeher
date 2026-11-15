import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useReducedMotion } from "framer-motion";
import {
  ArrowLeft,
  ArrowRight,
  Bookmark,
  BookmarkCheck,
  Check,
  CheckCircle2,
  Clock,
  Code2,
  Copy,
  FileText,
  ListChecks,
  LogIn,
  Lock,
  RotateCcw,
  Send,
  Sparkles,
  XCircle,
} from "lucide-react";
import { api } from "../../services/api";
import { useAsync } from "../../hooks";
import { useAuth } from "../../context/AuthContext";
import { useToast } from "../../context/ToastContext";
import {
  Alert,
  Badge,
  Button,
  Card,
  EmptyState,
  ErrorState,
  IconButton,
  LevelBadge,
  Loading,
  ProgressBar,
  Skeleton,
  SkeletonText,
} from "../../components/ui";
import { lessonMinutes, normalizeCurriculum } from "./CourseDetail";
import "./learning.css";

const KIND_ICONS = { text: FileText, code: Code2, quiz: ListChecks };
const NOTE_VARIANTS = { warning: "warning", success: "success", danger: "error", error: "error", info: "info" };

/** Minimal keyword/string/comment tokenizer — no syntax-highlight dependency is installed. */
const TOKEN_PATTERN =
  /(\/\/[^\n]*|#[^\n]*)|("(?:[^"\\\n]|\\.)*"|'(?:[^'\\\n]|\\.)*'|`(?:[^`\\]|\\.)*`)|(\b(?:const|let|var|function|return|if|else|for|while|import|export|from|class|new|await|async|try|catch|def|elif|with|as|pass|raise|not|and|or|None|True|False|self|this|null|undefined|true|false)\b)|(\b\d+(?:\.\d+)?\b)|([A-Za-z_$][\w$]*(?=\())/g;

function tokenize(code) {
  const tokens = [];
  let cursor = 0;
  let match;
  TOKEN_PATTERN.lastIndex = 0;
  while ((match = TOKEN_PATTERN.exec(code))) {
    if (match.index > cursor) tokens.push({ text: code.slice(cursor, match.index) });
    const cls = match[1] ? "tk-com" : match[2] ? "tk-str" : match[3] ? "tk-key" : match[4] ? "tk-num" : "tk-fn";
    tokens.push({ text: match[0], cls });
    cursor = match.index + match[0].length;
  }
  if (cursor < code.length) tokens.push({ text: code.slice(cursor) });
  return tokens;
}

async function copyToClipboard(text) {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      return true;
    }
  } catch {
    // Clipboard permission denied — fall through to the legacy path.
  }
  try {
    const area = document.createElement("textarea");
    area.value = text;
    area.setAttribute("readonly", "");
    area.style.position = "fixed";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.select();
    const ok = document.execCommand("copy");
    document.body.removeChild(area);
    return ok;
  } catch {
    return false;
  }
}

function CodeExample({ language, code }) {
  const toast = useToast();
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    const ok = await copyToClipboard(code);
    if (ok) {
      setCopied(true);
      toast.success("Code example copied.");
      setTimeout(() => setCopied(false), 2000);
    } else {
      toast.error("Your browser blocked clipboard access — select the code and copy it manually.");
    }
  }

  return (
    <div className="code-block ch-code">
      <div className="code-block__bar">
        <span>{language || "example"}</span>
        <button type="button" className="ch-code__copy" onClick={handleCopy}>
          {copied ? <Check size={14} aria-hidden="true" /> : <Copy size={14} aria-hidden="true" />}
          {copied ? "Copied" : "Copy code"}
        </button>
      </div>
      <pre tabIndex={0} aria-label={`Code example${language ? ` in ${language}` : ""}`}>
        <code>
          {tokenize(code).map((token, index) =>
            token.cls ? (
              <span key={index} className={token.cls}>
                {token.text}
              </span>
            ) : (
              <span key={index}>{token.text}</span>
            )
          )}
        </code>
      </pre>
    </div>
  );
}

function Block({ block, lessonTitle }) {
  const text = block.text ?? block.content ?? block.body ?? "";
  switch (block.type) {
    case "heading": {
      const depth = Math.min(4, Math.max(2, Number(block.level) || 2));
      const Tag = `h${depth}`;
      return <Tag className="lp__block-heading">{text}</Tag>;
    }
    case "list": {
      const items = block.items ?? block.list ?? [];
      const Tag = block.ordered ? "ol" : "ul";
      return (
        <Tag className="lp__list">
          {items.map((item, index) => (
            <li key={index}>{typeof item === "string" ? item : (item.text ?? item.label ?? "")}</li>
          ))}
        </Tag>
      );
    }
    case "code":
      return <CodeExample language={block.language} code={block.code ?? text ?? ""} />;
    case "note":
      return (
        <Alert variant={NOTE_VARIANTS[block.variant] ?? "info"} title={block.title || "Note"}>
          {text}
        </Alert>
      );
    case "image":
      return (
        <figure className="lp__figure">
          <img
            src={block.url ?? block.src ?? ""}
            alt={block.alt || block.caption || `${lessonTitle}: diagram`}
            loading="lazy"
          />
          {block.caption && <figcaption className="muted">{block.caption}</figcaption>}
        </figure>
      );
    case "paragraph":
    default:
      return <p className="lp__paragraph">{text}</p>;
  }
}

const CHOSEN_KEYS = ["chosen_index", "choice_index", "selected_index", "user_answer_index", "user_answer", "chosen", "selected"];
const RIGHT_KEYS = ["correct_index", "right_answer_index", "correct_choice_index", "expected_index", "correct_answer"];

function readIndex(source, keys) {
  if (!source) return null;
  for (const key of keys) {
    const value = source[key];
    if (value == null) continue;
    if (typeof value === "number") return value;
    if (typeof value === "string" && /^\d+$/.test(value)) return Number(value);
    if (typeof value === "object") {
      if (typeof value.index === "number") return value.index;
      const nested = readIndex(value, keys);
      if (nested != null) return nested;
    }
  }
  return null;
}

function normalizeQuiz(raw) {
  if (!raw) return null;
  return {
    id: raw.id,
    title: raw.title ?? "Knowledge check",
    instructions: raw.instructions ?? raw.description ?? null,
    passScore: raw.pass_score ?? raw.passing_score ?? raw.pass_percent ?? null,
    questions: (raw.questions ?? []).map((question, index) => ({
      id: question.id ?? index,
      text: question.text ?? question.prompt ?? question.question ?? question.title ?? `Question ${index + 1}`,
      hint: question.hint ?? null,
      choices: (question.choices ?? question.options ?? question.answers ?? []).map((choice, choiceIndex) => ({
        index: choiceIndex,
        text:
          typeof choice === "string"
            ? choice
            : (choice.text ?? choice.label ?? choice.content ?? choice.body ?? String(choice)),
      })),
    })),
  };
}

function Quiz({ quiz, onReload }) {
  const normalized = useMemo(() => normalizeQuiz(quiz), [quiz]);
  const [answers, setAnswers] = useState({});
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const questions = normalized?.questions ?? [];

  if (!normalized || questions.length === 0) {
    return (
      <EmptyState
        icon={ListChecks}
        title="No questions published yet"
        description="This lesson is marked as a quiz, but the API returned no questions. Once an instructor adds them you can score it here."
        action={
          <Button variant="ghost" onClick={onReload}>
            <RotateCcw size={15} /> Reload the lesson
          </Button>
        }
      />
    );
  }

  if (!normalized.id) {
    return (
      <Alert variant="warning" title="This quiz cannot be scored yet">
        The lesson references a quiz but the API sent no quiz id, so there is nothing to submit yet. Reload
        the lesson after the instructor republishes it.
      </Alert>
    );
  }

  const answered = questions.filter((question) => answers[question.id] != null).length;
  const ready = answered === questions.length;

  async function handleSubmit(event) {
    event.preventDefault();
    if (!ready) return;
    setBusy(true);
    setError(null);
    try {
      const response = await api.post(
        `/learning/quizzes/${normalized.id}/submit/`,
        { answers: questions.map((question) => ({ question_id: question.id, choice_index: answers[question.id] })) }
      );
      setResult(response);
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  }

  const results = Array.isArray(result?.results) ? result.results : [];

  return (
    <section className="quiz" aria-labelledby="quiz-title">
      <header className="quiz__head">
        <h2 id="quiz-title">{normalized.title}</h2>
        <span className="muted">
          {questions.length} question{questions.length === 1 ? "" : "s"}
          {normalized.passScore != null && ` · pass at ${normalized.passScore}%`}
        </span>
        {normalized.instructions && <p className="quiz__intro">{normalized.instructions}</p>}
      </header>

      <form className="quiz__form" onSubmit={handleSubmit}>
        <ol className="quiz__list">
          {questions.map((question, questionIndex) => {
            const resultRow =
              results.find(
                (row, rowIndex) =>
                  String(row?.question_id ?? row?.question ?? "") === String(question.id) ||
                  Number(row?.position) === questionIndex + 1 ||
                  (results.length === questions.length && rowIndex === questionIndex)
              ) ?? null;
            const chosen = readIndex(resultRow, CHOSEN_KEYS);
            const right = readIndex(resultRow, RIGHT_KEYS);
            const isCorrect = Boolean(resultRow?.correct ?? resultRow?.is_correct);

            return (
              <li key={question.id}>
                <fieldset className="quiz-q">
                  <legend className="quiz-q__legend">
                    <span className={`quiz-q__num ${resultRow ? (isCorrect ? "quiz-q__num--yes" : "quiz-q__num--no") : ""}`}>
                      {resultRow ? (
                        isCorrect ? (
                          <CheckCircle2 size={16} aria-hidden="true" />
                        ) : (
                          <XCircle size={16} aria-hidden="true" />
                        )
                      ) : (
                        questionIndex + 1
                      )}
                      <span className="sr-only">
                        {resultRow ? (isCorrect ? "Correct" : "Incorrect") : "Unanswered"}
                      </span>
                    </span>
                    {question.text}
                  </legend>
                  {question.hint && <p className="muted quiz-q__hint">{question.hint}</p>}
                  <div className="quiz-q__choices" role="radiogroup" aria-label={question.text}>
                    {question.choices.map((choice) => {
                      const checked = answers[question.id] === choice.index;
                      const isChosen = chosen === choice.index;
                      const isRight = right === choice.index;
                      return (
                        <label
                          key={choice.index}
                          className={
                            `quiz-choice ${checked ? "quiz-choice--on" : ""} ` +
                            (resultRow ? (isRight ? "quiz-choice--right" : isChosen ? "quiz-choice--wrong" : "") : "")
                          }
                        >
                          <input
                            type="radio"
                            name={`question-${question.id}`}
                            value={choice.index}
                            checked={checked}
                            onChange={() => setAnswers((current) => ({ ...current, [question.id]: choice.index }))}
                            disabled={busy || Boolean(resultRow)}
                          />
                          <span className="quiz-choice__text">{choice.text}</span>
                          {resultRow && isChosen && <span className="quiz-choice__flag">your answer</span>}
                          {resultRow && isRight && <span className="quiz-choice__flag quiz-choice__flag--right">correct</span>}
                        </label>
                      );
                    })}
                  </div>
                </fieldset>
              </li>
            );
          })}
        </ol>

        {error && (
          <Alert variant="error" title="The quiz could not be scored">
            {error.detail || error.message || "Check your connection and submit again."}
          </Alert>
        )}

        {!result && (
          <div className="quiz__foot">
            <p className="muted" id="quiz-progress">
              {answered === questions.length
                ? "All questions answered — submit to get your score."
                : `Answer all ${questions.length} questions to submit (${answered} done).`}
            </p>
            <Button type="submit" loading={busy} disabled={!ready} aria-describedby="quiz-progress">
              <Send size={16} /> Submit answers
            </Button>
          </div>
        )}
      </form>

      {result && (
        <Card className="quiz__result" as="section" aria-live="polite">
          <div className="quiz__score">
            <div>
              <span className="field__label">Score</span>
              <span className="quiz__score-value">{Math.round(Number(result.score_percent ?? 0))}%</span>
            </div>
            <Badge variant={result.passed ? "success" : "danger"}>
              {result.passed ? "Passed" : "Not passed yet"}
            </Badge>
          </div>
          <ProgressBar value={Number(result.score_percent ?? 0)} label={`${result.correct ?? 0} of ${result.total ?? questions.length} correct`} showValue />
          <p className="muted" style={{ fontSize: "var(--fs-sm)" }}>
            {result.passed
              ? "Nice work — mark the lesson complete to record it and earn the XP."
              : "Review the corrections below and try again. Only verified passes award XP, and repeats cannot double-count."}
          </p>
          <div className="row">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setResult(null);
                setAnswers({});
              }}
            >
              <RotateCcw size={15} /> Try again
            </Button>
          </div>
        </Card>
      )}
    </section>
  );
}

function SignInGate() {
  return (
    <div className="container lp">
      <h1 className="lp__title">Lesson reader</h1>
      <Card className="lp__gate">
        <LogIn size={22} aria-hidden="true" />
        <h2>Sign in to open this lesson</h2>
        <p>
          Lesson progress, bookmarks, quiz scores and XP are stored against your CodeHer account. Create
          one free — it takes under a minute — then come back to this link.
        </p>
        <div className="row">
          <Button to="/signin">Sign in</Button>
          <Button variant="ghost" to="/signup">
            Create a free account
          </Button>
          <Button variant="link" to="/learning">
            Browse the catalog
          </Button>
        </div>
      </Card>
    </div>
  );
}

export default function LessonPlayer() {
  const { courseId, lessonId } = useParams();
  const { isAuthenticated } = useAuth();
  const toast = useToast();
  const reduce = useReducedMotion();

  const lessonReq = useAsync((signal) => api.get(`/learning/lessons/${lessonId}/`, { signal }), [lessonId], {
    skip: !isAuthenticated,
  });
  const curriculumReq = useAsync(
    (signal) => api.get(`/learning/courses/${courseId}/curriculum/`, { signal }),
    [courseId],
    { skip: !isAuthenticated || !courseId }
  );

  const lesson = lessonReq.data;
  const [completed, setCompleted] = useState(false);
  const [award, setAward] = useState(null);
  const [bookmarked, setBookmarked] = useState(false);
  const [busyComplete, setBusyComplete] = useState(false);
  const [busyBookmark, setBusyBookmark] = useState(false);

  useEffect(() => {
    if (!lesson) return;
    setCompleted(Boolean(lesson.completed ?? lesson.is_completed));
    setBookmarked(Boolean(lesson.bookmarked));
    setAward(null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lesson?.id, lesson?.completed, lesson?.bookmarked]);

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: reduce ? "auto" : "smooth" });
  }, [lessonId, reduce]);

  const modules = useMemo(() => normalizeCurriculum(curriculumReq.data), [curriculumReq.data]);
  const siblings = useMemo(() => modules.flatMap((module) => module.lessons), [modules]);
  const currentIndex = siblings.findIndex((item) => String(item.id) === String(lessonId));
  const previous = currentIndex > 0 ? siblings[currentIndex - 1] : null;
  const next = currentIndex >= 0 && currentIndex < siblings.length - 1 ? siblings[currentIndex + 1] : null;

  const courseTitle = lesson?.course?.title || lesson?.course_title || null;
  const courseHref = `/learning/${lesson?.course?.slug ?? lesson?.course?.id ?? courseId}`;

  async function markComplete() {
    setBusyComplete(true);
    try {
      const response = await api.post(`/learning/lessons/${lesson.id}/complete/`);
      const isComplete = typeof response?.completed === "boolean" ? response.completed : true;
      setCompleted(isComplete);
      setAward({ xp: Number(response?.xp_awarded ?? 0), duplicate: Boolean(response?.duplicate) });
      if (response?.duplicate) {
        toast.info("Already marked complete — no XP added again.");
      } else if (Number(response?.xp_awarded ?? 0) > 0) {
        toast.success(`+${response.xp_awarded} XP for completing this lesson.`);
      } else {
        toast.success("Lesson marked complete.");
      }
      curriculumReq.reload();
    } catch (error) {
      if (error?.status === 403) {
        toast.warning("Enroll in this course to record your progress.");
      } else {
        toast.error(error?.detail || error?.message || "Could not save your progress.");
      }
    } finally {
      setBusyComplete(false);
    }
  }

  async function toggleBookmark() {
    setBusyBookmark(true);
    const optimistic = !bookmarked;
    setBookmarked(optimistic);
    try {
      const response = await api.post(`/learning/lessons/${lesson.id}/bookmark/`);
      const value = typeof response?.bookmarked === "boolean" ? response.bookmarked : optimistic;
      setBookmarked(value);
    } catch (error) {
      setBookmarked(!optimistic);
      toast.error(error?.detail || error?.message || "Could not save that bookmark.");
    } finally {
      setBusyBookmark(false);
    }
  }

  if (!isAuthenticated) return <SignInGate />;

  if (lessonReq.error) {
    const forbidden = lessonReq.error.status === 403;
    return (
      <div className="container lp">
        <h1 className="lp__title">Lesson unavailable</h1>
        {forbidden ? (
          <Alert variant="warning" title="You need access to this course first">
            {lessonReq.error.detail || "The API returned 403 for this lesson. Enroll from the course page."}
            <Button size="sm" variant="outline" to={`/learning/${courseId}`} style={{ marginLeft: "var(--sp-3)" }}>
              Open the course page
            </Button>
          </Alert>
        ) : (
          <ErrorState error={lessonReq.error} onRetry={lessonReq.reload} title="This lesson could not be loaded" />
        )}
        <Button variant="ghost" to={courseHref} style={{ marginTop: "var(--sp-4)" }}>
          <ArrowLeft size={15} /> Back to the course
        </Button>
      </div>
    );
  }

  if (lessonReq.loading && !lesson) {
    return (
      <div className="container lp" aria-busy="true">
        <Loading label="Opening your lesson" />
        <Skeleton className="skeleton--title" />
        <SkeletonText lines={6} />
      </div>
    );
  }

  const blocks = Array.isArray(lesson?.body_blocks) ? lesson.body_blocks : [];
  const kind = lesson?.kind ?? "text";
  const KindIcon = KIND_ICONS[kind] ?? FileText;
  const minutes = lessonMinutes(lesson?.estimated_minutes);

  return (
    <div className="lp">
      <div className="container lp__bar">
        <nav className="cd__crumbs" aria-label="Breadcrumb">
          <Link to="/learning">Learning</Link>
          <span aria-hidden="true">/</span>
          <Link to={courseHref}>{courseTitle || "Course"}</Link>
          <span aria-hidden="true">/</span>
          <span>Lesson {lesson?.position ?? (currentIndex >= 0 ? currentIndex + 1 : 1)}</span>
        </nav>
        <div className="row" style={{ gap: "var(--sp-2)" }}>
          {lesson?.xp > 0 && (
            <Badge variant="brand">
              <Sparkles size={12} aria-hidden="true" /> {lesson.xp} XP
            </Badge>
          )}
          <IconButton
            variant="ghost"
            label={bookmarked ? "Remove this lesson from your bookmarks" : "Bookmark this lesson"}
            aria-pressed={bookmarked}
            disabled={busyBookmark}
            onClick={toggleBookmark}
          >
            {bookmarked ? <BookmarkCheck size={17} /> : <Bookmark size={17} />}
          </IconButton>
        </div>
      </div>

      <div className="container lp__layout">
        <article className="lp__main">
          <header className="lp__header">
            <div className="lp__kind">
              <KindIcon size={15} aria-hidden="true" />
              {kind === "quiz" ? "Quiz" : kind === "code" ? "Code-along" : "Reading"}
              {minutes && (
                <span className="muted">
                  <Clock size={13} aria-hidden="true" /> {minutes}
                </span>
              )}
            </div>
            <h1 className="lp__title">{lesson?.title}</h1>
            {lesson?.module_title && <p className="muted">{lesson.module_title}</p>}
          </header>

          {blocks.length === 0 && kind !== "quiz" && (
            <Alert variant="info" title="This lesson has no written content yet">
              The lesson exists in the curriculum but no body blocks are published. The actions below still
              record your progress.
            </Alert>
          )}

          <div className="lp__blocks stack">
            {blocks.map((block, index) => (
              <Block key={block.id ?? `${block.type}-${index}`} block={block} lessonTitle={lesson?.title ?? "this lesson"} />
            ))}
          </div>

          {lesson?.code_example?.code && (
            <section className="lp__section" aria-labelledby="example-title">
              <h2 id="example-title">Code example</h2>
              <CodeExample language={lesson.code_example.language} code={lesson.code_example.code} />
            </section>
          )}

          {kind === "quiz" && (
            <section className="lp__section" aria-label="Knowledge check">
              <Quiz key={lesson?.id} quiz={lesson?.quiz} onReload={lessonReq.reload} />
            </section>
          )}

          {award && (
            <Alert variant={award.duplicate ? "info" : "success"}>
              {award.duplicate
                ? "You already completed this lesson, so no XP was awarded again."
                : award.xp > 0
                  ? `+${award.xp} XP added to your account.`
                  : "Lesson recorded as complete."}
            </Alert>
          )}

          <footer className="lp__done">
            <Button size="lg" variant={completed ? "outline" : "primary"} loading={busyComplete} onClick={markComplete}>
              {completed ? <CheckCircle2 size={17} aria-hidden="true" /> : <Check size={17} aria-hidden="true" />}
              {completed ? "Completed — well done" : "Mark complete"}
            </Button>
            {completed && next && (
              <Button size="lg" to={`/learning/${courseId}/lessons/${next.id}`}>
                Next lesson: {next.title} <ArrowRight size={17} />
              </Button>
            )}
            {!completed && (
              <span className="muted" style={{ fontSize: "var(--fs-sm)" }}>
                Completion is verified by the server and can only award XP once.
              </span>
            )}
          </footer>

          <nav className="lp__pager" aria-label="Lesson navigation">
            {previous ? (
              <Button variant="ghost" size="sm" to={`/learning/${courseId}/lessons/${previous.id}`}>
                <ArrowLeft size={15} /> {previous.title}
              </Button>
            ) : (
              <span className="muted" style={{ fontSize: "var(--fs-sm)" }}>
                This is the first lesson.
              </span>
            )}
            {next ? (
              <Button variant="ghost" size="sm" to={`/learning/${courseId}/lessons/${next.id}`}>
                {next.title} <ArrowRight size={15} />
              </Button>
            ) : (
              <span className="muted" style={{ fontSize: "var(--fs-sm)" }}>
                You reached the last lesson of this course.
              </span>
            )}
          </nav>
        </article>

        <aside className="lp__side" aria-label="Lessons in this course">
          <div className="lp__side-head">
            <Link className="lp__side-course" to={courseHref}>
              {courseTitle || "Course contents"}
            </Link>
            <span className="muted" style={{ fontSize: "var(--fs-xs)" }}>
              {siblings.length > 0 ? `${siblings.filter((item) => item.completed).length}/${siblings.length} done` : ""}
            </span>
          </div>

          {curriculumReq.error ? (
            <p className="muted lp__side-note">
              The lesson list is not available to your account right now
              {curriculumReq.error.status === 403 ? " — enroll in the course to see every lesson." : "."}
            </p>
          ) : curriculumReq.loading && !curriculumReq.data ? (
            <div className="stack" aria-hidden="true">
              <Skeleton className="skeleton--text" />
              <Skeleton className="skeleton--text" />
              <Skeleton className="skeleton--text" style={{ width: "70%" }} />
            </div>
          ) : modules.length === 0 ? (
            <p className="muted lp__side-note">No other lessons are published for this course yet.</p>
          ) : (
            <div className="lp__toc">
              {modules.map((module, moduleIndex) => (
                <div key={module.id} className="lp__toc-group">
                  <span className="lp__toc-title">
                    Module {moduleIndex + 1} · {module.title}
                  </span>
                  <ol className="lp__toc-list">
                    {module.lessons.map((item) => {
                      const isCurrent = String(item.id) === String(lessonId);
                      const Icon = KIND_ICONS[item.kind] ?? FileText;
                      return (
                        <li key={item.id}>
                          <Link
                            to={`/learning/${courseId}/lessons/${item.id}`}
                            aria-current={isCurrent ? "page" : undefined}
                            className={`lp__toc-link ${isCurrent ? "lp__toc-link--on" : ""} ${item.locked ? "lp__toc-link--locked" : ""}`}
                            title={item.locked ? item.locked_reason ?? "Locked" : undefined}
                          >
                            <Icon size={14} aria-hidden="true" />
                            <span className="lp__toc-text">{item.title}</span>
                            {item.locked && <Lock className="lp__toc-lock" size={12} aria-hidden="true" />}
                            {item.completed && <CheckCircle2 className="lp__toc-check" size={13} aria-hidden="true" />}
                            {isCurrent && <span className="sr-only">(current lesson)</span>}
                          </Link>
                        </li>
                      );
                    })}
                  </ol>
                </div>
              ))}
            </div>
          )}

          {lesson?.course_level && (
            <p className="lp__side-level">
              <LevelBadge level={lesson.course_level} />
              <span className="muted">Course level</span>
            </p>
          )}
        </aside>
      </div>
    </div>
  );
}
