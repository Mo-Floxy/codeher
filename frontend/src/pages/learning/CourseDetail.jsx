import { useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useReducedMotion } from "framer-motion";
import {
  ArrowRight,
  Award,
  BookOpen,
  Bookmark,
  BookmarkCheck,
  Check,
  CheckCircle2,
  ChevronDown,
  Clock,
  Code2,
  FileText,
  Layers,
  ListChecks,
  Lock,
  LogIn,
  Sparkles,
  Users,
} from "lucide-react";
import { api } from "../../services/api";
import { useAsync } from "../../hooks";
import { useAuth } from "../../context/AuthContext";
import { useToast } from "../../context/ToastContext";
import {
  Alert,
  Button,
  Card,
  Chip,
  ErrorState,
  IconButton,
  LevelBadge,
  ProgressBar,
  Skeleton,
  SkeletonText,
  UserCell,
} from "../../components/ui";
import { Reveal } from "../../components/motion";
import "./learning.css";

const KINDS = {
  text: { label: "Reading", icon: FileText },
  code: { label: "Code-along", icon: Code2 },
  quiz: { label: "Quiz", icon: ListChecks },
};

export function lessonMinutes(value) {
  const minutes = Number(value);
  return Number.isFinite(minutes) && minutes > 0 ? `${minutes} min` : null;
}

function toLesson(raw, index) {
  const moduleRef = typeof raw.module === "object" ? raw.module : null;
  return {
    id: raw.id,
    title: raw.title ?? `Lesson ${index + 1}`,
    kind: raw.kind ?? "text",
    position: raw.position ?? index + 1,
    estimated_minutes: raw.estimated_minutes ?? null,
    xp: Number(raw.xp ?? 0),
    completed: Boolean(raw.completed),
    bookmarked: Boolean(raw.bookmarked),
    locked: Boolean(raw.locked),
    locked_reason: raw.locked_reason ?? raw.lock_reason ?? null,
    moduleId: moduleRef?.id ?? raw.module ?? raw.module_id ?? null,
    moduleTitle: moduleRef?.title ?? null,
  };
}

/** The curriculum document may come back as modules-with-lessons or one flat lesson list.
 *  Shared with the lesson player, which needs the same sibling list for its sidebar. */
export function normalizeCurriculum(payload) {
  if (!payload) return [];
  const root = Array.isArray(payload.results) ? payload.results : payload;
  const rawModules = Array.isArray(root)
    ? root
    : (root.modules ?? root.results ?? []).filter((item) => item && typeof item === "object");

  if (Array.isArray(rawModules) && rawModules.length) {
    return rawModules.map((module, index) => ({
      id: module.id ?? `module-${index}`,
      title: module.title ?? `Module ${index + 1}`,
      description: module.description ?? null,
      lessons: (module.lessons ?? module.items ?? []).map(toLesson),
    }));
  }

  const loose = (Array.isArray(root.lessons) ? root.lessons : []).map(toLesson);
  const buckets = new Map();
  loose.forEach((lesson) => {
    const key = lesson.moduleId ?? "general";
    if (!buckets.has(key)) {
      buckets.set(key, { id: key, title: lesson.moduleTitle ?? `Module ${buckets.size + 1}`, description: null, lessons: [] });
    }
    buckets.get(key).lessons.push(lesson);
  });
  return [...buckets.values()];
}

function LessonRow({ lesson, courseId, canOpen, lockReason, busy, onToggleBookmark }) {
  const kind = KINDS[lesson.kind] ?? KINDS.text;
  const KindIcon = kind.icon;
  const minutes = lessonMinutes(lesson.estimated_minutes);

  return (
    <li className={`lesson-row ${canOpen ? "" : "lesson-row--off"}`.trim()}>
      <span className="lesson-row__kind" aria-hidden="true">
        <KindIcon size={15} />
      </span>
      <div className="lesson-row__main">
        {canOpen ? (
          <Link className="lesson-row__link" to={`/learning/${courseId}/lessons/${lesson.id}`}>
            <span className="lesson-row__title">{lesson.title}</span>
            <span className="sr-only">Open {kind.label.toLowerCase()} lesson</span>
          </Link>
        ) : (
          <span className="lesson-row__title">{lesson.title}</span>
        )}
        <span className="lesson-row__tags">
          <Chip as="span">{kind.label}</Chip>
          {minutes && <span className="muted">{minutes}</span>}
          {lesson.xp > 0 && <span className="muted">{lesson.xp} XP</span>}
          {lesson.completed && (
            <span className="lesson-row__done">
              <CheckCircle2 size={14} aria-hidden="true" /> Completed
            </span>
          )}
        </span>
        {!canOpen && lockReason && (
          <span className="lesson-row__lock" title={lockReason}>
            <Lock size={12} aria-hidden="true" /> {lockReason}
          </span>
        )}
      </div>
      <IconButton
        className="lesson-row__bookmark"
        size="sm"
        variant="ghost"
        label={lesson.bookmarked ? `Remove bookmark from ${lesson.title}` : `Bookmark ${lesson.title}`}
        aria-pressed={lesson.bookmarked}
        disabled={busy}
        onClick={onToggleBookmark}
      >
        {lesson.bookmarked ? <BookmarkCheck size={16} /> : <Bookmark size={16} />}
      </IconButton>
    </li>
  );
}

function ModuleSection({ module, index, courseId, canOpenLessons, bookmarkOverrides, busyId, onToggleBookmark }) {
  const [forceOpen, setForceOpen] = useState(null);
  const isOpen = forceOpen ?? index === 0;
  const done = module.lessons.filter((lesson) => lesson.completed).length;
  const moduleProgress = module.lessons.length ? (done / module.lessons.length) * 100 : 0;

  return (
    <div className="module">
      <h3 className="module__heading">
        <button
          type="button"
          className="module__toggle"
          aria-expanded={isOpen}
          aria-controls={`module-panel-${module.id}`}
          id={`module-head-${module.id}`}
          onClick={() => setForceOpen(!isOpen)}
        >
          <ChevronDown size={17} className={`module__chev ${isOpen ? "" : "module__chev--closed"}`.trim()} aria-hidden="true" />
          <span className="module__name">
            <span className="module__index">Module {index + 1}</span>
            {module.title}
          </span>
          <span className="module__count">
            {done}/{module.lessons.length} done
          </span>
        </button>
      </h3>

      <div
        id={`module-panel-${module.id}`}
        role="region"
        aria-labelledby={`module-head-${module.id}`}
        className="module__panel"
        hidden={!isOpen}
      >
        {module.description && <p className="module__desc">{module.description}</p>}
        {canOpenLessons && done > 0 && (
          <ProgressBar value={moduleProgress} thin label="Lessons you completed in this module" showValue />
        )}
        {module.lessons.length === 0 ? (
          <p className="muted" style={{ fontSize: "var(--fs-sm)" }}>
            This module has no lessons published yet.
          </p>
        ) : (
          <ul className="lesson-list">
            {module.lessons.map((raw) => {
              const lesson = { ...raw, bookmarked: bookmarkOverrides[raw.id] ?? raw.bookmarked };
              return (
                <LessonRow
                  key={lesson.id}
                  lesson={lesson}
                  courseId={courseId}
                  canOpen={canOpenLessons && !lesson.locked}
                  lockReason={
                    lesson.locked
                      ? lesson.locked_reason ?? "Finish an earlier lesson in this module to unlock this one."
                      : "Enroll to open this lesson."
                  }
                  busy={busyId === lesson.id}
                  onToggleBookmark={() => onToggleBookmark(lesson)}
                />
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
}

export default function CourseDetail() {
  const { slug } = useParams();
  const { isAuthenticated } = useAuth();
  const toast = useToast();
  const reduce = useReducedMotion();
  const [enrollBusy, setEnrollBusy] = useState(false);
  const [bookmarkBusy, setBookmarkBusy] = useState(null);
  const [bookmarkOverrides, setBookmarkOverrides] = useState({});

  // The detail route accepts either a slug or a pk in this position.
  const courseReq = useAsync((signal) => api.get(`/learning/courses/${slug}/`, { signal }), [slug]);
  const course = courseReq.data;
  const courseId = course?.id;

  const curriculumReq = useAsync(
    (signal) => api.get(`/learning/courses/${courseId}/curriculum/`, { signal }),
    [courseId],
    { skip: !courseId }
  );

  const modules = useMemo(() => normalizeCurriculum(curriculumReq.data), [curriculumReq.data]);
  const lessons = useMemo(() => modules.flatMap((module) => module.lessons), [modules]);
  const totalXp = lessons.reduce((sum, lesson) => sum + lesson.xp, 0);
  const totalMinutes = lessons.reduce((sum, lesson) => sum + (Number(lesson.estimated_minutes) || 0), 0);
  const quizCount = lessons.filter((lesson) => lesson.kind === "quiz").length;

  const resumeLesson = useMemo(
    () => lessons.find((lesson) => !lesson.locked && !lesson.completed) ?? lessons.find((lesson) => !lesson.locked),
    [lessons]
  );

  async function toggleEnroll() {
    const enrolling = !course.is_enrolled;
    const previous = course;
    courseReq.setData({
      ...course,
      is_enrolled: enrolling,
      enrolled_count: Math.max(0, (course.enrolled_count ?? 0) + (enrolling ? 1 : -1)),
    });
    setEnrollBusy(true);
    try {
      const response = enrolling
        ? await api.post(`/learning/courses/${course.id}/enroll/`)
        : await api.del(`/learning/courses/${course.id}/enroll/`);
      const enrolled = typeof response?.enrolled === "boolean" ? response.enrolled : enrolling;
      courseReq.setData((current) => ({
        ...current,
        is_enrolled: enrolled,
        progress_percent: enrolled ? current.progress_percent : 0,
      }));
      if (!enrolled) setBookmarkOverrides({});
      curriculumReq.reload();
      toast.success(enrolled ? "You are enrolled — your progress now saves to your account." : "You left this course.");
    } catch (error) {
      courseReq.setData(previous);
      toast.error(error?.detail || error?.message || "Could not update your enrollment.");
    } finally {
      setEnrollBusy(false);
    }
  }

  async function toggleBookmark(lesson) {
    setBookmarkBusy(lesson.id);
    const optimistic = !lesson.bookmarked;
    setBookmarkOverrides((current) => ({ ...current, [lesson.id]: optimistic }));
    try {
      const response = await api.post(`/learning/lessons/${lesson.id}/bookmark/`);
      const bookmarked = typeof response?.bookmarked === "boolean" ? response.bookmarked : optimistic;
      setBookmarkOverrides((current) => ({ ...current, [lesson.id]: bookmarked }));
      if (bookmarked !== optimistic) toast.warning("Bookmark state changed — try again.");
    } catch (error) {
      setBookmarkOverrides((current) => ({ ...current, [lesson.id]: !optimistic }));
      toast.error(error?.detail || error?.message || "Could not save that bookmark.");
    } finally {
      setBookmarkBusy(null);
    }
  }

  if (courseReq.error) {
    const forbidden = courseReq.error.status === 403;
    return (
      <div className="container cd">
        <nav className="cd__crumbs" aria-label="Breadcrumb">
          <Link to="/learning">Learning</Link>
        </nav>
        <h1 className="cd__title">Course unavailable</h1>
        {forbidden ? (
          <Alert variant="warning" title="This course is not open to your account">
            {courseReq.error.detail || "The API returned 403 for this course. Enroll through the catalog or ask an admin to publish it."}
          </Alert>
        ) : (
          <ErrorState error={courseReq.error} onRetry={courseReq.reload} title="We could not load this course" />
        )}
        <Button variant="ghost" to="/learning" style={{ marginTop: "var(--sp-4)" }}>
          Back to the catalog
        </Button>
      </div>
    );
  }

  if (courseReq.loading && !course) {
    return (
      <div className="container cd" aria-busy="true">
        <Skeleton style={{ height: 220, borderRadius: "var(--r-lg)" }} />
        <div className="stack" style={{ marginTop: "var(--sp-5)", gap: "var(--sp-3)" }}>
          <Skeleton className="skeleton--title" />
          <SkeletonText lines={3} />
        </div>
      </div>
    );
  }

  if (!course) {
    return (
      <div className="container cd">
        <h1 className="cd__title">Course not found</h1>
        <p className="lead">The API returned no course for “{slug}”. It may have been unpublished.</p>
        <Button to="/learning" style={{ marginTop: "var(--sp-4)" }}>
          Back to the catalog
        </Button>
      </div>
    );
  }

  const enrolled = Boolean(course?.is_enrolled);
  const progress = Number(course?.progress_percent ?? 0);
  const pathTitle = typeof course?.path === "object" ? course.path?.title : course?.path;
  const pathValue = typeof course?.path === "object" ? (course.path?.slug ?? course.path?.id) : course?.path;

  return (
    <div className="cd">
      <header className="cd__hero">
        <div className="container">
          <nav className="cd__crumbs" aria-label="Breadcrumb">
            <Link to="/learning">Learning</Link>
            {pathTitle && (
              <>
                <span aria-hidden="true">/</span>
                <Link to={`/learning?path=${encodeURIComponent(pathValue ?? "")}`}>{pathTitle}</Link>
              </>
            )}
            <span aria-hidden="true">/</span>
            <span>{course.title}</span>
          </nav>

          <div className="cd__hero-grid">
            <div className="cd__hero-copy">
              <span className="eyebrow">{course.category || "Course"}</span>
              <h1 className="cd__title">{course.title}</h1>
              {course.subtitle && <p className="lead">{course.subtitle}</p>}

              <ul className="cd__facts">
                <li>
                  <LevelBadge level={course.level} />
                </li>
                <li>
                  <Clock size={15} aria-hidden="true" /> {Number(course.duration_hours) || 0} h
                </li>
                <li>
                  <BookOpen size={15} aria-hidden="true" />{" "}
                  {course.lesson_count ?? course.total_lessons ?? lessons.length} lessons
                </li>
                <li>
                  <Users size={15} aria-hidden="true" /> {course.enrolled_count ?? 0} enrolled
                </li>
                {pathTitle && (
                  <li>
                    <Layers size={15} aria-hidden="true" /> {pathTitle}
                  </li>
                )}
              </ul>

              <div className="cd__instructor">
                <span className="field__label">Taught by</span>
                <UserCell
                  user={course.instructor}
                  subtitle={course.instructor?.headline}
                  to={course.instructor?.id ? `/members/${course.instructor.id}` : undefined}
                />
              </div>

              <div className="cd__actions">
                {isAuthenticated ? (
                  <Button size="lg" variant={enrolled ? "outline" : "primary"} loading={enrollBusy} onClick={toggleEnroll}>
                    {enrolled ? "Leave this course" : "Enroll — it is free"}
                  </Button>
                ) : (
                  <Button size="lg" to="/signin">
                    <LogIn size={17} /> Sign in to enroll
                  </Button>
                )}
                {enrolled && resumeLesson && (
                  <Button size="lg" variant="ghost" to={`/learning/${course.id}/lessons/${resumeLesson.id}`}>
                    {progress > 0 ? "Continue learning" : "Start first lesson"} <ArrowRight size={17} />
                  </Button>
                )}
              </div>

              {enrolled && (
                <div className="cd__progress">
                  <ProgressBar
                    value={progress}
                    label={`${course.completed_lesson_count ?? 0} of ${lessons.length || course.lesson_count || 0} lessons completed`}
                    showValue
                  />
                </div>
              )}
            </div>

            <Reveal y={24} delay={0.1}>
              <Card className="cd__aside" glow={!reduce}>
                <h2 className="cd__aside-title">What you can earn</h2>
                <ul className="cd__earn">
                  <li>
                    <Sparkles size={18} aria-hidden="true" />
                    <span>
                      <strong>{totalXp > 0 ? `${totalXp} XP` : "XP per lesson"}</strong>
                      <span className="muted">Awarded by the server as you complete lessons and pass quizzes.</span>
                    </span>
                  </li>
                  <li>
                    <Award size={18} aria-hidden="true" />
                    <span>
                      <strong>Completion certificate</strong>
                      <span className="muted">Issued when every lesson is done — print it from your certificates page.</span>
                    </span>
                  </li>
                  <li>
                    <ListChecks size={18} aria-hidden="true" />
                    <span>
                      <strong>{quizCount > 0 ? `${quizCount} scored quiz${quizCount === 1 ? "" : "zes"}` : "Practice exercises"}</strong>
                      <span className="muted">{totalMinutes > 0 ? `About ${totalMinutes} minutes of focused work.` : "Work through it at your own pace."}</span>
                    </span>
                  </li>
                </ul>
              </Card>
            </Reveal>
          </div>
        </div>
      </header>

      <div className="container cd__body">
        {Array.isArray(course.objectives) && course.objectives.length > 0 && (
          <section className="cd__section" aria-labelledby="objectives-title">
            <h2 id="objectives-title">What you will be able to do</h2>
            <ul className="cd__objectives">
              {course.objectives.map((objective) => (
                <li key={objective}>
                  <Check size={16} aria-hidden="true" />
                  <span>{objective}</span>
                </li>
              ))}
            </ul>
          </section>
        )}

        {course.description && (
          <section className="cd__section" aria-labelledby="about-course-title">
            <h2 id="about-course-title">About this course</h2>
            <p className="lead">{course.description}</p>
          </section>
        )}

        <section className="cd__section" aria-labelledby="curriculum-title">
          <div className="cd__section-head">
            <h2 id="curriculum-title">Curriculum</h2>
            <span className="muted">
              {modules.length} module{modules.length === 1 ? "" : "s"} · {lessons.length} lesson
              {lessons.length === 1 ? "" : "s"}
            </span>
          </div>

          {!enrolled && (
            <Alert variant="info" title="You are previewing the outline">
              Lessons below are listed but not open yet. Enrolling unlocks the reader, saves your completion
              state, and lets you earn XP and a certificate.
              <Button
                size="sm"
                variant="outline"
                onClick={isAuthenticated ? toggleEnroll : undefined}
                to={isAuthenticated ? undefined : "/signin"}
                loading={enrollBusy}
                style={{ marginLeft: "var(--sp-3)" }}
              >
                {isAuthenticated ? "Enroll now" : "Sign in to enroll"}
              </Button>
            </Alert>
          )}

          {curriculumReq.error ? (
            curriculumReq.error.status === 403 ? (
              <Alert variant="warning" title="The curriculum needs your enrollment">
                {curriculumReq.error.detail || "The API returned 403 for this curriculum."}
              </Alert>
            ) : (
              <ErrorState error={curriculumReq.error} onRetry={curriculumReq.reload} title="The curriculum could not be loaded" />
            )
          ) : curriculumReq.loading && !curriculumReq.data ? (
            <Card className="stack">
              <Skeleton className="skeleton--title" />
              <SkeletonText lines={4} />
            </Card>
          ) : modules.length === 0 ? (
            <Card className="cd__empty">
              <p>
                This course has no published modules yet. Instructors add them over time — check back soon
                or pick another course from the catalog.
              </p>
              <Button variant="ghost" to="/learning">
                Browse the catalog
              </Button>
            </Card>
          ) : (
            <div className="modules">
              {modules.map((module, index) => (
                <ModuleSection
                  key={module.id}
                  module={module}
                  index={index}
                  courseId={course.id}
                  canOpenLessons={enrolled && isAuthenticated}
                  bookmarkOverrides={bookmarkOverrides}
                  busyId={bookmarkBusy}
                  onToggleBookmark={toggleBookmark}
                />
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
