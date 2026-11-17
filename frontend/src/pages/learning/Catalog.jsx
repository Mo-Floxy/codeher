import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useReducedMotion } from "framer-motion";
import { BookOpen, Clock, Layers, LogIn, RotateCcw, SearchX, Users } from "lucide-react";
import { api, endpoints } from "../../services/api";
import { useAsync, useDebouncedValue } from "../../hooks";
import { CourseCover } from "../../components/CourseCover";
import { Stagger } from "../../components/motion";
import {
  Avatar,
  Button,
  Card,
  Chip,
  EmptyState,
  ErrorState,
  Field,
  LevelBadge,
  Pagination,
  ProgressBar,
  SearchInput,
  Select,
  Skeleton,
  SkeletonList,
} from "../../components/ui";
import { useAuth } from "../../context/AuthContext";
import "./learning.css";

const PAGE_SIZE = 12;

const LEVELS = [
  { value: "beginner", label: "Beginner" },
  { value: "intermediate", label: "Intermediate" },
  { value: "advanced", label: "Advanced" },
];

// Ordering tokens are the DRF `?ordering=` values the course viewset declares.
const SORTS = [
  { value: "-created_at", label: "Newest first" },
  { value: "-enrolled_count", label: "Most enrolled" },
  { value: "duration_hours", label: "Shortest duration" },
  { value: "title", label: "Title A–Z" },
];

function unwrap(payload) {
  if (Array.isArray(payload)) return payload;
  return payload?.results ?? [];
}

function formatHours(value) {
  const hours = Number(value);
  if (!Number.isFinite(hours) || hours <= 0) return null;
  if (hours < 1) return `${Math.round(hours * 60)} min`;
  return `${Number(hours.toFixed(1))} h`;
}

function CourseCard({ course, resumeTo }) {
  const slug = course.slug ?? course.id;
  const href = `/learning/${slug}`;
  const lessons = course.lesson_count ?? course.total_lessons;
  const duration = formatHours(course.duration_hours);
  const progress = Number(course.progress_percent ?? 0);
  const enrolled = Boolean(course.is_enrolled);

  return (
    <Card className="course-card" hover>
      <div className="course-card__thumb">
        {/* Artwork only: the title link below names the card, so the image stays decorative. */}
        {course.thumbnail ? (
          <img src={course.thumbnail} alt="" loading="lazy" />
        ) : (
          <CourseCover path={course.path} />
        )}
        <span className="course-card__thumb-level">
          <LevelBadge level={course.level} />
        </span>
      </div>

      <div className="course-card__body">
        <h3 className="course-card__title">
          <Link to={href}>{course.title}</Link>
        </h3>
        <p className="course-card__desc">{course.subtitle || course.description}</p>

        <ul className="course-card__facts">
          {duration && (
            <li>
              <Clock size={14} aria-hidden="true" /> {duration}
            </li>
          )}
          {lessons != null && (
            <li>
              <BookOpen size={14} aria-hidden="true" /> {lessons} lesson{lessons === 1 ? "" : "s"}
            </li>
          )}
          <li>
            <Users size={14} aria-hidden="true" /> {course.enrolled_count ?? 0} enrolled
          </li>
          {course.category && <li className="course-card__category">{course.category}</li>}
        </ul>

        <div className="course-card__by">
          <Avatar user={course.instructor} size="sm" />
          <span className="muted">{course.instructor?.display_name || "CodeHer mentor"}</span>
        </div>

        {enrolled && (
          <ProgressBar
            value={progress}
            thin
            label={
              progress >= 100
                ? "Course complete"
                : `${course.completed_lesson_count ?? 0} of ${lessons ?? course.completed_lesson_count ?? 0} lessons done`
            }
            showValue
          />
        )}

        <div className="course-card__foot">
          {enrolled && resumeTo ? (
            <Button size="sm" to={resumeTo}>
              Continue <BookOpen size={15} />
            </Button>
          ) : enrolled ? (
            <Button size="sm" to={href}>
              {progress > 0 ? "Resume course" : "Open the curriculum"} <BookOpen size={15} />
            </Button>
          ) : (
            <Button size="sm" variant="outline" to={href}>
              Course overview
            </Button>
          )}
        </div>
      </div>
    </Card>
  );
}

export default function Catalog() {
  const { isAuthenticated, isBooting } = useAuth();
  const reduce = useReducedMotion();
  const [params, setParams] = useSearchParams();

  const search = params.get("search") ?? "";
  const level = params.get("level") ?? "";
  const path = params.get("path") ?? "";
  const ordering = params.get("ordering") ?? SORTS[0].value;
  const page = Math.max(1, Number(params.get("page") || 1));

  const [draft, setDraft] = useState(search);
  const debouncedSearch = useDebouncedValue(draft, 350);

  // Back/forward navigation re-seeds the input from the URL.
  useEffect(() => setDraft(search), [search]);

  function writeParams(patch) {
    setParams(
      (current) => {
        const next = new URLSearchParams(current);
        for (const [key, value] of Object.entries(patch)) {
          if (value === null || value === undefined || value === "") next.delete(key);
          else next.set(key, String(value));
        }
        return next;
      },
      { replace: true }
    );
  }

  useEffect(() => {
    if (debouncedSearch === search) return;
    writeParams({ search: debouncedSearch.trim(), page: null });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedSearch]);

  const courses = useAsync(
    (signal) =>
      api.get(endpoints.courses, {
        signal,
        params: {
          search: search || undefined,
          level: level || undefined,
          path: path || undefined,
          ordering,
          page,
          page_size: PAGE_SIZE,
        },
      }),
    [search, level, path, ordering, page]
  );

  const paths = useAsync((signal) => api.get(endpoints.paths, { signal, params: { page_size: 24 } }), []);
  // Enrollments give the lesson to resume from; the course card itself has no lesson pointer.
  const enrollments = useAsync((signal) => api.get(endpoints.enrollments, { signal, params: { page_size: 50 } }), [], {
    skip: !isAuthenticated,
  });

  const rows = useMemo(() => unwrap(courses.data), [courses.data]);
  const count = courses.data?.count ?? rows.length;
  const pathRows = useMemo(() => unwrap(paths.data), [paths.data]);

  const resumeByCourse = useMemo(() => {
    const map = {};
    for (const enrollment of unwrap(enrollments.data)) {
      const courseId = enrollment.course?.id ?? enrollment.course_id ?? enrollment.course;
      const lessonId =
        enrollment.next_lesson?.id ??
        enrollment.next_lesson_id ??
        enrollment.resume_lesson?.id ??
        enrollment.resume_lesson_id ??
        enrollment.lesson?.id ??
        enrollment.lesson_id;
      const slug = enrollment.course?.slug;
      if (courseId == null || lessonId == null) continue;
      map[courseId] = { lessonId, slug };
    }
    return map;
  }, [enrollments.data]);

  const firstIndex = count === 0 ? 0 : (page - 1) * PAGE_SIZE + 1;
  const lastIndex = Math.min(page * PAGE_SIZE, count);
  const hasFilters = Boolean(search || level || path || params.get("page")) || ordering !== SORTS[0].value;

  return (
    <div className="cat">
      <header className="cat__head container">
        <span className="eyebrow">Learning</span>
        <h1>Course catalog</h1>
        <p className="lead">
          Guided courses in HTML, CSS, JavaScript, React, Python, Django and MySQL — each one built
          from modules, lessons, code examples and quizzes, with your progress stored in your account.
        </p>
      </header>

      <section className="container" aria-label="Search and filter courses">
        <Card className="cat__filters">
          <div className="cat__filters-top">
            <Field label="Search courses" htmlFor="catalog-search" className="cat__search">
              <SearchInput
                id="catalog-search"
                label="Search courses"
                placeholder="Try “react”, “django”, “accessibility”…"
                value={draft}
                onChange={setDraft}
              />
            </Field>
            <Field label="Sort by" htmlFor="catalog-sort" className="cat__sort">
              <Select
                id="catalog-sort"
                value={ordering}
                options={SORTS}
                onChange={(event) => writeParams({ ordering: event.target.value, page: null })}
              />
            </Field>
          </div>

          <div className="cat__filters-groups">
            <div className="stack" style={{ gap: "var(--sp-2)" }}>
              <span className="field__label" id="level-filter-label">
                Skill level
              </span>
              <div className="row" role="group" aria-labelledby="level-filter-label">
                <Chip selected={!level} onClick={() => writeParams({ level: null, page: null })}>
                  All levels
                </Chip>
                {LEVELS.map((item) => (
                  <Chip
                    key={item.value}
                    selected={level === item.value}
                    onClick={() => writeParams({ level: level === item.value ? null : item.value, page: null })}
                  >
                    {item.label}
                  </Chip>
                ))}
              </div>
            </div>

            <div className="stack" style={{ gap: "var(--sp-2)" }}>
              <span className="field__label" id="path-filter-label">
                Learning path
              </span>
              {paths.loading && !paths.data ? (
                <div className="row" aria-hidden="true">
                  <Skeleton style={{ width: 96, height: 26, borderRadius: 999 }} />
                  <Skeleton style={{ width: 120, height: 26, borderRadius: 999 }} />
                  <Skeleton style={{ width: 84, height: 26, borderRadius: 999 }} />
                </div>
              ) : pathRows.length === 0 ? (
                <span className="muted" style={{ fontSize: "var(--fs-xs)" }}>
                  No learning paths published yet.
                </span>
              ) : (
                <div className="row" role="group" aria-labelledby="path-filter-label">
                  <Chip selected={!path} onClick={() => writeParams({ path: null, page: null })}>
                    All paths
                  </Chip>
                  {pathRows.map((item) => {
                    const value = item.slug ?? item.id;
                    return (
                      <Chip
                        key={value}
                        selected={path === String(value)}
                        onClick={() => writeParams({ path: path === String(value) ? null : value, page: null })}
                      >
                        {item.title}
                      </Chip>
                    );
                  })}
                </div>
              )}
            </div>

            {hasFilters && (
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setParams(new URLSearchParams(), { replace: true })}
              >
                <RotateCcw size={14} /> Clear filters
              </Button>
            )}
          </div>
        </Card>
      </section>

      <section className="container cat__results" aria-label="Courses">
        <div className="cat__toolbar" aria-live="polite">
          {courses.loading ? (
            <span className="muted">Loading courses…</span>
          ) : (
            <span className="muted">
              {count === 0
                ? "No courses match these filters"
                : `Showing ${firstIndex}–${lastIndex} of ${count} course${count === 1 ? "" : "s"}`}
              {search && ` for “${search}”`}
              {level && ` · ${level}`}
              {path && ` · path ${path}`}
            </span>
          )}
          {isAuthenticated === false && !isBooting && (
            <Button size="sm" variant="link" to="/signin">
              <LogIn size={14} /> Sign in to keep your progress
            </Button>
          )}
        </div>

        {courses.loading && !courses.data ? (
          <SkeletonList count={6} height={330} />
        ) : courses.error ? (
          <ErrorState
            error={courses.error}
            onRetry={courses.reload}
            title="The course list could not be loaded"
          />
        ) : rows.length === 0 ? (
          <EmptyState
            icon={SearchX}
            title="Nothing here yet"
            description="No course matches this combination of search text, level and path. Loosen a filter to see more."
            action={
              hasFilters ? (
                <Button variant="ghost" onClick={() => setParams(new URLSearchParams(), { replace: true })}>
                  <RotateCcw size={15} /> Reset filters
                </Button>
              ) : (
                <Button variant="ghost" to="/challenges">
                  <Layers size={15} /> Practice with a challenge instead
                </Button>
              )
            }
          />
        ) : (
          <>
            <Stagger className="grid-auto cat__grid" as="div">
              {rows.map((course) => {
                const resume = resumeByCourse[course.id];
                return (
                  <Stagger.Item key={course.id}>
                    <CourseCard
                      course={course}
                      // The player route is keyed by course id so the curriculum call never has to
                      // resolve a slug.
                      resumeTo={resume ? `/learning/${course.id}/lessons/${resume.lessonId}` : null}
                    />
                  </Stagger.Item>
                );
              })}
            </Stagger>
            <Pagination
              count={count}
              page={page}
              pageSize={PAGE_SIZE}
              onPageChange={(next) => {
                writeParams({ page: next > 1 ? next : null });
                window.scrollTo({ top: 0, behavior: reduce ? "auto" : "smooth" });
              }}
            />
          </>
        )}
      </section>
    </div>
  );
}
