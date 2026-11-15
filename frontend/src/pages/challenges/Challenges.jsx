import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useReducedMotion } from "framer-motion";
import {
  ArrowRight,
  CheckCircle2,
  Code2,
  ListChecks,
  SearchX,
  Sparkles,
  Target,
  Trophy,
  Users,
  Zap,
} from "lucide-react";
import { api, endpoints } from "../../services/api";
import { useAsync, useDebouncedValue } from "../../hooks";
import { Reveal, Stagger } from "../../components/motion";
import {
  Badge,
  Button,
  Card,
  Chip,
  ChipRow,
  EmptyState,
  ErrorState,
  Field,
  LevelBadge,
  Pagination,
  SearchInput,
  Select,
  Skeleton,
  SkeletonList,
  Tabs,
  UserCell,
} from "../../components/ui";
import { useAuth } from "../../context/AuthContext";
import "./challenges.css";

const DIFFICULTIES = [
  { value: "beginner", label: "Beginner" },
  { value: "intermediate", label: "Intermediate" },
  { value: "advanced", label: "Advanced" },
];

const CATEGORIES = [
  { value: "javascript", label: "JavaScript" },
  { value: "python", label: "Python" },
  { value: "algorithms", label: "Algorithms" },
  { value: "web development", label: "Web Development" },
];

const ORDERING = [
  { value: "points", label: "Most points" },
  { value: "difficulty", label: "Easiest first" },
  { value: "recent", label: "Recently added" },
  { value: "newest_solved", label: "Recently solved" },
];

const PAGE_SIZE = 12;

/** DRF serializers vary on list-vs-string fields; accept either shape instead of guessing one. */
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

function firstNumber(...values) {
  for (const value of values) {
    if (value === null || value === undefined || value === "") continue;
    const parsed = Number(value);
    if (!Number.isNaN(parsed)) return parsed;
  }
  return null;
}

/** Ratios arrive as either 0.42 or 42 depending on the serializer — normalise to a percentage. */
function toPercent(...values) {
  const raw = firstNumber(...values);
  if (raw === null) return null;
  return Math.round(raw <= 1 ? raw * 100 : raw);
}

function normalizeChallenge(row) {
  const languages = asList(row.languages ?? row.supported_languages ?? row.language);
  return {
    key: row.id ?? row.slug ?? row.title,
    id: row.id ?? row.slug,
    title: row.title ?? "Untitled challenge",
    excerpt: row.excerpt ?? row.short_description ?? row.description ?? "",
    difficulty: row.difficulty ?? row.level ?? "",
    categories: asList(row.categories ?? row.category ?? row.tags),
    languages,
    points: firstNumber(row.points, row.reward_points, row.xp) ?? 0,
    passRate: toPercent(row.pass_rate, row.acceptance_rate, row.success_rate),
    attempts: firstNumber(row.attempt_count, row.submissions_count, row.solvers_count),
    solved: Boolean(row.is_solved ?? row.solved ?? row.user_has_solved ?? row.has_solved),
  };
}

function leaderboardUser(row) {
  const source = row.user && typeof row.user === "object" ? row.user : {};
  return {
    display_name: row.display_name ?? source.display_name ?? source.username ?? "Member",
    username: row.username ?? source.username,
    avatar: row.avatar ?? source.avatar,
  };
}

function LeaderboardStrip() {
  const [period, setPeriod] = useState("weekly");
  const { data, loading, error, reload } = useAsync(
    (signal) => api.get(endpoints.challengeLeaderboard, { signal, params: { period } }),
    [period]
  );

  // The contract returns a bare array; keep tolerating a paginated envelope.
  const rows = useMemo(() => {
    const list = Array.isArray(data) ? data : (data?.results ?? []);
    return list.slice(0, 8);
  }, [data]);

  return (
    <Card className="leaderboard" aria-labelledby="leaderboard-title">
      <div className="leaderboard__head">
        <div className="stack" style={{ gap: 4 }}>
          <span className="eyebrow">
            <Trophy size={13} /> Community standings
          </span>
          <h2 id="leaderboard-title">Challenge leaderboard</h2>
          <p className="muted" style={{ fontSize: "var(--fs-xs)" }}>
            Points come only from verified passing submissions, so a solved challenge counts once.
          </p>
        </div>
        <Tabs
          items={[
            { value: "weekly", label: "This week" },
            { value: "alltime", label: "All time" },
          ]}
          value={period}
          onChange={setPeriod}
          ariaLabel="Leaderboard period"
        />
      </div>

      {loading ? (
        <div className="stack" style={{ gap: 8 }}>
          {Array.from({ length: 5 }).map((_, index) => (
            <Skeleton key={index} style={{ height: 44 }} />
          ))}
        </div>
      ) : error ? (
        <ErrorState
          error={error}
          onRetry={reload}
          title="The leaderboard could not be loaded"
        />
      ) : rows.length === 0 ? (
        <EmptyState
          icon={Trophy}
          title="No standings yet"
          description={
            period === "weekly"
              ? "Nobody has a passing submission in the current week. Be the first."
              : "The all-time table fills up as members pass challenges."
          }
        />
      ) : (
        <ol className="leaderboard__list">
          {rows.map((row, index) => {
            const user = leaderboardUser(row);
            const points = firstNumber(row.points, row.score, row.total_points) ?? 0;
            const solved = firstNumber(row.solved_count, row.solves) ?? 0;
            return (
              <li
                key={`${row.rank ?? "r"}-${user.display_name}-${index}`}
                className={`leaderboard__row ${index < 3 ? "leaderboard__row--top" : ""}`.trim()}
              >
                <span className="leaderboard__rank" aria-label={`Rank ${row.rank ?? index + 1}`}>
                  {row.rank ?? index + 1}
                </span>
                <UserCell
                  user={user}
                  to={row.user && typeof row.user === "object" && row.user.id ? `/members/${row.user.id}` : undefined}
                  subtitle={user.username ? `@${user.username}` : undefined}
                />
                <span className="leaderboard__points">
                  {points.toLocaleString()} pts
                </span>
                <span className="leaderboard__solved">{solved} solved</span>
              </li>
            );
          })}
        </ol>
      )}
    </Card>
  );
}

export default function Challenges() {
  const { isAuthenticated } = useAuth();
  const reduce = useReducedMotion();
  const [searchParams, setSearchParams] = useSearchParams();

  const difficulty = searchParams.get("difficulty") ?? "";
  const category = searchParams.get("category") ?? "";
  const ordering = ORDERING.some((option) => option.value === searchParams.get("ordering"))
    ? searchParams.get("ordering")
    : "points";
  const pageParam = Number(searchParams.get("page"));
  const page = Number.isFinite(pageParam) && pageParam > 0 ? pageParam : 1;

  const [searchInput, setSearchInput] = useState(searchParams.get("search") ?? "");
  const search = useDebouncedValue(searchInput.trim(), 400);

  // Push the settled keystrokes into the URL so filters stay shareable and reloadable.
  useEffect(() => {
    if ((searchParams.get("search") ?? "") === search) return;
    const next = new URLSearchParams(searchParams);
    if (search) next.set("search", search);
    else next.delete("search");
    next.delete("page");
    setSearchParams(next, { replace: true });
  }, [search, searchParams, setSearchParams]);

  const updateParam = (key, value) => {
    const next = new URLSearchParams(searchParams);
    if (value) next.set(key, value);
    else next.delete(key);
    if (key !== "page") next.delete("page");
    setSearchParams(next);
  };

  const clearFilters = () => {
    setSearchParams(new URLSearchParams());
    setSearchInput("");
  };

  const { data, loading, error, reload } = useAsync(
    (signal) =>
      api.get(endpoints.challenges, {
        signal,
        params: { difficulty, category, search, ordering, page, page_size: PAGE_SIZE },
      }),
    [difficulty, category, search, ordering, page]
  );

  const items = useMemo(
    () => (data?.results ?? (Array.isArray(data) ? data : [])).map(normalizeChallenge),
    [data]
  );
  const count = firstNumber(data?.count) ?? items.length;
  const hasFilters = Boolean(search || difficulty || category || ordering !== "points");

  const activeChips = [
    search ? `“${search}”` : null,
    difficulty ? DIFFICULTIES.find((d) => d.value === difficulty)?.label : null,
    category ? CATEGORIES.find((c) => c.value === category)?.label : null,
  ].filter(Boolean);

  return (
    <div className="container challenges-page">
      <header className="challenges-page__intro">
        <span className="eyebrow">
          <Code2 size={13} /> Sandboxed practice
        </span>
        <h1>Code challenges</h1>
        <p className="lead">
          Short, scored exercises in JavaScript and Python. Every solution runs inside an isolated
          runner with CPU, memory and network limits — never in the app server — so you can break
          things freely, then submit for points when the sample tests go green.
        </p>
        <ChipRow>
          <Chip>
            <ListChecks size={13} /> Sample tests while you work
          </Chip>
          <Chip>
            <Target size={13} /> Hidden tests only on submit
          </Chip>
          <Chip>
            <Zap size={13} /> Points for a first solve
          </Chip>
        </ChipRow>
      </header>

      <Reveal as="section" aria-label="Filter challenges" className="filters">
        <div className="filters__row">
          <Field label="Search challenges" htmlFor="challenge-search">
            <SearchInput
              id="challenge-search"
              label="Search challenges"
              value={searchInput}
              onChange={setSearchInput}
              placeholder="Try “recursion”, “dict”, “sort”…"
            />
          </Field>
          <Field label="Sort by" htmlFor="challenge-ordering" className="filters__sort">
            <Select
              id="challenge-ordering"
              value={ordering}
              onChange={(event) => updateParam("ordering", event.target.value)}
              options={ORDERING}
            />
          </Field>
        </div>

        <div className="filters__group">
          <span className="filters__label" id="difficulty-label">
            Difficulty
          </span>
          <div className="row" role="group" aria-labelledby="difficulty-label" style={{ gap: "var(--sp-2)" }}>
            <Chip onClick={() => updateParam("difficulty", "")} selected={difficulty === ""}>
              All levels
            </Chip>
            {DIFFICULTIES.map((option) => (
              <Chip
                key={option.value}
                onClick={() =>
                  updateParam("difficulty", difficulty === option.value ? "" : option.value)
                }
                selected={difficulty === option.value}
              >
                {option.label}
              </Chip>
            ))}
          </div>
        </div>

        <div className="filters__group">
          <span className="filters__label" id="category-label">
            Category
          </span>
          <ChipRow>
            <span className="row" role="group" aria-labelledby="category-label" style={{ gap: "var(--sp-2)" }}>
              <Chip onClick={() => updateParam("category", "")} selected={category === ""}>
                All categories
              </Chip>
              {CATEGORIES.map((option) => (
                <Chip
                  key={option.value}
                  onClick={() =>
                    updateParam("category", category === option.value ? "" : option.value)
                  }
                  selected={category === option.value}
                >
                  {option.label}
                </Chip>
              ))}
            </span>
          </ChipRow>
        </div>

        <div className="filters__meta">
          <span aria-live="polite">
            {loading
              ? "Searching challenges…"
              : error
                ? "Results unavailable"
                : `${count} challenge${count === 1 ? "" : "s"}${
                    activeChips.length ? ` for ${activeChips.join(" · ")}` : ""
                  }`}
          </span>
          {hasFilters && (
            <Button variant="link" size="sm" onClick={clearFilters}>
              Clear filters
            </Button>
          )}
        </div>
      </Reveal>

      <section aria-labelledby="challenge-results-title">
        <h2 className="sr-only" id="challenge-results-title">
          Challenges
        </h2>

        {loading ? (
          <SkeletonList count={6} height={210} />
        ) : error ? (
          <ErrorState
            error={error}
            onRetry={reload}
            title="We could not load the challenges"
          />
        ) : items.length === 0 ? (
          <EmptyState
            icon={SearchX}
            title="No challenge matches these filters"
            description={
              hasFilters
                ? "Try a different keyword, widen the difficulty or pick another category."
                : "No challenges exist yet. They are authored in the admin area and appear here once published."
            }
            action={
              hasFilters ? (
                <Button variant="ghost" onClick={clearFilters}>
                  Clear all filters
                </Button>
              ) : undefined
            }
          />
        ) : (
          <>
            <Stagger className="grid-auto">
              {items.map((item) => (
                <Stagger.Item key={item.key}>
                  <Card
                    hover
                    to={`/challenges/${item.id}`}
                    className={`challenge-card ${item.solved ? "challenge-card--solved" : ""}`.trim()}
                  >
                    <div className="challenge-card__head">
                      <LevelBadge level={item.difficulty} />
                      {isAuthenticated && item.solved && (
                        <Badge variant="success">
                          <CheckCircle2 size={12} /> Solved
                        </Badge>
                      )}
                    </div>
                    <h3>{item.title}</h3>
                    {item.excerpt && <p className="challenge-card__excerpt">{item.excerpt}</p>}
                    <ChipRow>
                      {item.categories.slice(0, 3).map((tag) => (
                        <Chip key={tag}>{tag}</Chip>
                      ))}
                      {item.languages.slice(0, 2).map((language) => (
                        <Chip key={language}>{language}</Chip>
                      ))}
                    </ChipRow>
                    <div className="challenge-card__stats">
                      <span className="challenge-card__stat challenge-card__stat--points">
                        <Zap size={13} /> {item.points} pts
                      </span>
                      {item.passRate !== null && (
                        <span className="challenge-card__stat challenge-card__stat--rate">
                          <Users size={13} /> {item.passRate}% pass rate
                        </span>
                      )}
                      {item.attempts !== null && (
                        <span className="challenge-card__stat">
                          <Sparkles size={13} /> {item.attempts.toLocaleString()} attempts
                        </span>
                      )}
                      {!reduce && (
                        <ArrowRight size={15} style={{ marginLeft: "auto", color: "var(--violet)" }} aria-hidden="true" />
                      )}
                    </div>
                  </Card>
                </Stagger.Item>
              ))}
            </Stagger>
            <Pagination
              count={count}
              page={page}
              pageSize={PAGE_SIZE}
              onPageChange={(next) => {
                updateParam("page", next > 1 ? String(next) : "");
                window.scrollTo({ top: 0, behavior: reduce ? "auto" : "smooth" });
              }}
            />
          </>
        )}
      </section>

      <Reveal>
        <LeaderboardStrip />
      </Reveal>
    </div>
  );
}
