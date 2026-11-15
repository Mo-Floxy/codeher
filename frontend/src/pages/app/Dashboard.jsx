import { useMemo } from "react";
import { Link } from "react-router-dom";
import { useReducedMotion } from "framer-motion";
import {
  ArrowRight,
  BookOpen,
  CalendarDays,
  CheckCircle2,
  Code2,
  Compass,
  Flame,
  Medal,
  MessagesSquare,
  Network,
  Sparkles,
  Target,
  Trophy,
  Users,
} from "lucide-react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api, endpoints } from "../../services/api";
import { useAsync } from "../../hooks";
import {
  Badge,
  Button,
  Card,
  EmptyState,
  ErrorState,
  LevelBadge,
  ProgressBar,
  SectionHeading,
  Skeleton,
  Stat,
} from "../../components/ui";
import {
  asList,
  dateKeyPart,
  formatRelative,
  num,
  recentDateKeys,
  resolveRef,
  shortDayLabel,
  sum,
  todayKey,
} from "./helpers";
import "./app.css";

const SERIES = { minutes: "#a855f7", lessons: "#22d3ee" };

function DashboardSkeleton() {
  return (
    <div className="app-page" aria-busy="true">
      <Skeleton style={{ height: 30, width: "40%" }} />
      <Skeleton style={{ height: 140 }} />
      <div className="stat-grid">
        {[0, 1, 2, 3].map((key) => (
          <Skeleton key={key} style={{ height: 110 }} />
        ))}
      </div>
      <div className="dash-grid">
        <Skeleton style={{ height: 320 }} />
        <Skeleton style={{ height: 320 }} />
      </div>
    </div>
  );
}

function LevelCard({ data }) {
  const progress = num(data.level_progress_percent);
  // next_level_xp is the absolute threshold; the gap is what the learner wants to see.
  const remaining = num(data.xp_to_next_level);
  return (
    <Card className="level-card" glow>
      <span className="level-card__badge">
        <Trophy size={30} aria-hidden="true" />
      </span>
      <div>
        <span className="level-card__level">Level {num(data.level)}</span>
        <p className="level-card__xp" style={{ marginTop: 4 }}>
          {num(data.xp).toLocaleString()} XP
          {remaining > 0 ? ` · ${remaining.toLocaleString()} XP to your next level` : " · top level reached"}
        </p>
      </div>
      <div style={{ textAlign: "right" }}>
        <span className="stat__value">{progress}%</span>
        <div className="muted" style={{ fontSize: "var(--fs-xs)" }}>to next level</div>
      </div>
      <div className="level-card__progress">
        <ProgressBar
          value={progress}
          label={`Level ${num(data.level)} progress`}
          variant="success"
        />
      </div>
    </Card>
  );
}

function StatRow({ data }) {
  const completionRate = num(data.completion_rate_percent);
  const enrolled = num(data.enrolled_courses);
  const completedLessons = num(data.completed_lessons);
  const streak = data.streak ?? {};
  return (
    <div className="stat-grid">
      <Stat label="Enrolled courses" value={enrolled} icon={BookOpen} tone="brand" />
      <Stat label="Lessons completed" value={completedLessons} icon={CheckCircle2} tone="cyan" />
      <Stat
        label="Completion rate"
        value={`${completionRate}%`}
        icon={Target}
        tone="success"
        delta={enrolled > 0 ? `of ${enrolled} course${enrolled === 1 ? "" : "s"}` : "no courses yet"}
      />
      <Stat
        label="Day streak"
        value={num(streak.current)}
        icon={Flame}
        tone="pink"
        delta={`longest: ${num(streak.longest)} days`}
      />
    </div>
  );
}

function ContinueLearning({ items }) {
  if (!items.length) {
    return (
      <EmptyState
        icon={Compass}
        title="No course in progress"
        description="Pick up where you left off once you start a course. Browse the catalogue to enrol in your first path."
        action={
          <Button to="/learning">
            Browse courses <ArrowRight size={16} />
          </Button>
        }
      />
    );
  }
  return (
    <ul className="continue-list">
      {items.map((item, index) => {
        const course = resolveRef(item.course);
        const lesson = resolveRef(item.lesson);
        const progress = num(item.progress_percent);
        const position = item.next_position != null ? num(item.next_position) : null;
        return (
          <li key={`${course.id}-${lesson.id}-${index}`}>
            <Link className="continue-item" to={`/learning/${course.id}/lessons/${lesson.id}`}>
              <span className="continue-item__index" aria-hidden="true">
                {position != null ? position : index + 1}
              </span>
              <span style={{ minWidth: 0 }}>
                <span className="continue-item__title">{course.label || "Your course"}</span>
                <span className="continue-item__meta">
                  {lesson.id ? `Next: ${lesson.label}` : "Next lesson"}
                </span>
              </span>
              <span style={{ minWidth: 140, flex: "0 0 140px" }}>
                <ProgressBar value={progress} thin label={`${progress}%`} />
              </span>
            </Link>
          </li>
        );
      })}
    </ul>
  );
}

function WeeklyActivityChart({ activity }) {
  const reduce = useReducedMotion();
  const data = useMemo(
    () =>
      activity.map((point) => ({
        label: shortDayLabel(point.date),
        date: dateKeyPart(point.date) ?? String(point.date ?? ""),
        minutes: num(point.minutes),
        lessons: num(point.lessons_completed),
      })),
    [activity]
  );

  const totalMinutes = sum(data, "minutes");
  const totalLessons = sum(data, "lessons");
  const summary = `Weekly activity over the last ${data.length} days: ${totalMinutes} minutes studied and ${totalLessons} lessons completed.`;

  return (
    <div className="stack" style={{ gap: "var(--sp-4)" }}>
      <div className="chart-legend">
        <span>
          <span className="chart-legend__swatch" style={{ background: SERIES.minutes }} />
          Minutes
        </span>
        <span>
          <span className="chart-legend__swatch" style={{ background: SERIES.lessons }} />
          Lessons completed
        </span>
      </div>
      <div className="chart-frame" role="img" aria-label={summary}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -18 }}>
            <defs>
              <linearGradient id="minutesFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={SERIES.minutes} stopOpacity={0.5} />
                <stop offset="100%" stopColor={SERIES.minutes} stopOpacity={0.02} />
              </linearGradient>
              <linearGradient id="lessonsFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={SERIES.lessons} stopOpacity={0.4} />
                <stop offset="100%" stopColor={SERIES.lessons} stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,255,0.12)" vertical={false} />
            <XAxis dataKey="label" tick={{ fill: "#7e88ad", fontSize: 12 }} stroke="rgba(148,163,255,0.2)" />
            <YAxis
              yAxisId="minutes"
              tick={{ fill: "#7e88ad", fontSize: 12 }}
              stroke="rgba(148,163,255,0.2)"
              width={44}
            />
            <YAxis
              yAxisId="lessons"
              orientation="right"
              allowDecimals={false}
              tick={{ fill: "#7e88ad", fontSize: 12 }}
              stroke="rgba(148,163,255,0.2)"
              width={34}
            />
            <Tooltip
              contentStyle={{
                background: "#131a33",
                border: "1px solid rgba(167,139,250,0.42)",
                borderRadius: 12,
                fontSize: 13,
              }}
              labelStyle={{ color: "#f2f4ff" }}
              formatter={(value, name) => [value, name === "minutes" ? "Minutes" : "Lessons"]}
            />
            <Legend wrapperStyle={{ display: "none" }} />
            <Area
              yAxisId="minutes"
              type="monotone"
              dataKey="minutes"
              name="minutes"
              stroke={SERIES.minutes}
              strokeWidth={2}
              fill="url(#minutesFill)"
              isAnimationActive={!reduce}
            />
            <Area
              yAxisId="lessons"
              type="monotone"
              dataKey="lessons"
              name="lessons"
              stroke={SERIES.lessons}
              strokeWidth={2}
              fill="url(#lessonsFill)"
              isAnimationActive={!reduce}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
      <details className="chart-fallback">
        <summary>View the numbers as a table</summary>
        <div className="table-wrap" style={{ marginTop: "var(--sp-3)" }}>
          <table className="table">
            <caption className="sr-only">Daily study minutes and lessons completed</caption>
            <thead>
              <tr>
                <th scope="col">Date</th>
                <th scope="col">Minutes</th>
                <th scope="col">Lessons completed</th>
              </tr>
            </thead>
            <tbody>
              {data.map((row) => (
                <tr key={row.date || row.label}>
                  <td>{row.date || row.label}</td>
                  <td>{row.minutes}</td>
                  <td>{row.lessons}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </div>
  );
}

function StreakHeat({ streak }) {
  const activity = useMemo(() => new Set((streak.activity_dates ?? []).map((d) => dateKeyPart(d)).filter(Boolean)), [streak]);
  const endKey = dateKeyPart(streak.last_activity_date) ?? todayKey();
  const days = useMemo(() => recentDateKeys(endKey, 35), [endKey]);
  const today = todayKey();

  return (
    <div className="stack" style={{ gap: "var(--sp-3)" }}>
      <div className="heat-strip" role="img" aria-label={`Coding streak heat map: ${activity.size} active days in the last ${days.length}.`}>
        {days.map((key) => (
          <span
            key={key}
            className="heat-strip__cell"
            data-active={activity.has(key) ? "true" : "false"}
            data-today={key === today ? "true" : "false"}
            title={`${key}${activity.has(key) ? " · active" : ""}`}
          />
        ))}
      </div>
      <div className="heat-scale">
        <span className="heat-strip__cell" data-active="false" style={{ width: 12, height: 12 }} aria-hidden="true" />
        No activity
        <span className="heat-strip__cell" data-active="true" style={{ width: 12, height: 12, marginLeft: "var(--sp-4)" }} aria-hidden="true" />
        Active day
      </div>
    </div>
  );
}

function GoalRing({ goal }) {
  const target = num(goal.target_minutes);
  const actual = num(goal.actual_minutes);
  const pct = target > 0 ? Math.min(100, Math.round((actual / target) * 100)) : 0;
  const achieved = Boolean(goal.achieved) || (target > 0 && actual >= target);
  const radius = 52;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - pct / 100);

  return (
    <div className="goal-ring">
      <div role="img" aria-label={`Weekly goal: ${actual} of ${target} minutes (${pct}%). ${achieved ? "Achieved." : "In progress."}`}>
        <svg width="128" height="128" viewBox="0 0 128 128" className="goal-ring__svg">
          <defs>
            <linearGradient id="goalGradient" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor={achieved ? "#34d399" : "#8b5cf6"} />
              <stop offset="100%" stopColor={achieved ? "#22d3ee" : "#ec4899"} />
            </linearGradient>
          </defs>
          <circle className="goal-ring__track" cx="64" cy="64" r={radius} fill="none" strokeWidth="12" />
          <circle
            className="goal-ring__bar"
            cx="64"
            cy="64"
            r={radius}
            fill="none"
            strokeWidth="12"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
          />
          <text
            x="64"
            y="64"
            textAnchor="middle"
            dominantBaseline="central"
            transform="rotate(90 64 64)"
            fill="#f2f4ff"
            fontSize="24"
            fontWeight="800"
          >
            {pct}%
          </text>
        </svg>
      </div>
      <div className="stack" style={{ gap: 6, minWidth: 0 }}>
        <span className="goal-ring__value">{actual} / {target} min</span>
        <p className="muted" style={{ fontSize: "var(--fs-sm)" }}>
          {target <= 0
            ? "No weekly target set yet."
            : achieved
              ? "Goal reached — nicely done this week."
              : `${Math.max(0, target - actual)} more minutes to hit this week's target.`}
        </p>
        {achieved && (
          <span>
            <Badge variant="success">
              <CheckCircle2 size={13} aria-hidden="true" /> Achieved
            </Badge>
          </span>
        )}
      </div>
    </div>
  );
}

function RecommendedCourses({ courses }) {
  if (!courses.length) {
    return (
      <EmptyState
        icon={BookOpen}
        title="No recommendations yet"
        description="As you complete lessons, we surface courses matched to your path and skill level."
        action={<Button variant="ghost" to="/learning">Explore the catalogue</Button>}
      />
    );
  }
  return (
    <div className="grid-auto">
      {courses.slice(0, 4).map((course) => (
        <Card key={course.id} hover to={`/learning/${course.slug ?? course.id}`} as="article">
          <div className="course-card__thumb" style={{ aspectRatio: "16/7", marginBottom: "var(--sp-4)", background: "var(--brand-gradient-soft)" }}>
            {course.thumbnail ? <img src={course.thumbnail} alt="" /> : course.title}
          </div>
          <LevelBadge level={course.level} />
          <h3 style={{ fontSize: "var(--fs-md)", marginTop: "var(--sp-2)" }}>{course.title}</h3>
          {course.subtitle && <p style={{ fontSize: "var(--fs-sm)" }}>{course.subtitle}</p>}
          <div className="card__meta" style={{ marginTop: "var(--sp-3)" }}>
            <span>{num(course.duration_hours)}h</span>
            <span>·</span>
            <span>{num(course.total_lessons ?? course.lesson_count)} lessons</span>
          </div>
        </Card>
      ))}
    </div>
  );
}

function CommunityActivity({ posts }) {
  if (!posts.length) {
    return <EmptyState icon={MessagesSquare} title="Quiet in the community" description="Member posts, questions and showcases appear here as they arrive." />;
  }
  return (
    <ul className="mini-list">
      {posts.slice(0, 6).map((post, index) => {
        const author = post.author?.display_name || post.user?.display_name || post.display_name || "A member";
        return (
          <li key={post.id ?? index}>
            <Link className="mini-item" to={`/community/posts/${post.id}`}>
              <span className="mini-item__icon">
                <MessagesSquare size={16} aria-hidden="true" />
              </span>
              <span className="mini-item__grow">
                <span className="mini-item__title">{post.title || "Community post"}</span>
                <span className="mini-item__sub">
                  {author}
                  {post.created_at ? ` · ${formatRelative(post.created_at)}` : ""}
                </span>
              </span>
            </Link>
          </li>
        );
      })}
    </ul>
  );
}

function UpcomingEvents({ events }) {
  if (!events.length) {
    return <EmptyState icon={CalendarDays} title="No upcoming events" description="Community events, challenges and mentor sessions will show up here." />;
  }
  return (
    <ul className="mini-list">
      {events.map((event, index) => (
        <li key={event.id ?? index}>
          <div className="mini-item">
            <span className="mini-item__icon">
              <CalendarDays size={16} aria-hidden="true" />
            </span>
            <span className="mini-item__grow">
              <span className="mini-item__title">{event.title}</span>
              <span className="mini-item__sub">
                {event.kind ? `${event.kind} · ` : ""}
                {event.starts_at ? formatRelative(event.starts_at) : "Date to be announced"}
              </span>
            </span>
          </div>
        </li>
      ))}
    </ul>
  );
}

function EarnedBadges({ achievements }) {
  if (!achievements.length) {
    return (
      <EmptyState
        icon={Medal}
        title="No badges yet"
        description="Earn your first badge by completing a lesson, passing a quiz or publishing a project."
        action={<Button variant="ghost" to="/achievements">See the badge catalogue</Button>}
      />
    );
  }
  return (
    <ul className="mini-list">
      {achievements.slice(0, 6).map((achievement, index) => (
        <li key={achievement.badge ?? achievement.id ?? index}>
          <div className="mini-item">
            <span className="mini-item__icon">
              <Medal size={16} aria-hidden="true" />
            </span>
            <span className="mini-item__grow">
              <span className="mini-item__title">{achievement.title || achievement.badge || "Badge"}</span>
              <span className="mini-item__sub">
                {achievement.description ? `${achievement.description} · ` : ""}
                {achievement.earned_at ? `Earned ${formatRelative(achievement.earned_at)}` : "Earned"}
              </span>
            </span>
          </div>
        </li>
      ))}
    </ul>
  );
}

function Onboarding() {
  const steps = [
    { icon: Compass, title: "Choose a path", body: "Pick a guided track in HTML, CSS, JavaScript, React, Python, Django or MySQL.", to: "/learning", cta: "Browse courses" },
    { icon: Target, title: "Set a weekly goal", body: "Decide how many minutes a week you want to learn — we track it on your dashboard.", to: "/achievements", cta: "Set a goal" },
    { icon: Users, title: "Meet a mentor", body: "Request a mentor, get answers and stay accountable with real humans.", to: "/mentorship", cta: "Find a mentor" },
  ];
  return (
    <div className="onboard">
      <div>
        <span className="eyebrow">Welcome to CodeHer</span>
        <h2 className="onboard__title" style={{ marginTop: "var(--sp-3)" }}>Start your first path</h2>
        <p className="lead" style={{ marginTop: "var(--sp-2)" }}>
          You haven't enrolled in a course yet. Your XP, streak, progress and badges stay empty until
          you complete real lessons — nothing here is invented. Enrol in a course and this dashboard
          fills up with your activity.
        </p>
      </div>
      <div className="onboard__steps">
        {steps.map((step) => (
          <Card key={step.title} className="stack" style={{ gap: 8 }}>
            <span className="mini-item__icon">
              <step.icon size={18} aria-hidden="true" />
            </span>
            <strong style={{ fontSize: "var(--fs-md)" }}>{step.title}</strong>
            <p className="muted" style={{ fontSize: "var(--fs-sm)" }}>{step.body}</p>
            <Button variant="outline" size="sm" to={step.to}>
              {step.cta} <ArrowRight size={15} />
            </Button>
          </Card>
        ))}
      </div>
    </div>
  );
}

export default function Dashboard() {
  const { data, loading, error, reload } = useAsync((signal) => api.get(endpoints.dashboard, { signal }), []);

  const sections = useMemo(() => {
    if (!data) return null;
    return {
      continueLearning: asList(data.continue_learning),
      weeklyActivity: asList(data.weekly_activity),
      upcomingEvents: asList(data.upcoming_events),
      recommended: asList(data.recommended_courses),
      community: asList(data.community_activity),
      achievements: asList(data.achievements),
    };
  }, [data]);

  let heading = "Dashboard";
  if (data?.greeting) heading = data.greeting;

  return (
    <div className="app-page">
      <header className="app-page__head">
        <h1 className="app-page__title">{heading}</h1>
        <p className="app-page__sub">Your learning, streak and community — all from your own account.</p>
      </header>

      {loading ? <DashboardSkeleton /> : null}

      {!loading && error ? <ErrorState error={error} onRetry={reload} title="We couldn't load your dashboard" /> : null}

      {!loading && !error && data ? (
        <>
          {num(data.enrolled_courses) === 0 ? (
            <Onboarding />
          ) : (
            <>
              <LevelCard data={data} />
              <StatRow data={data} />
              <div className="dash-grid">
                <div className="dash-stack">
                  <Card className="stack" style={{ gap: "var(--sp-4)" }}>
                    <SectionHeadingInline icon={BookOpen} title="Continue learning" />
                    <ContinueLearning items={sections.continueLearning} />
                  </Card>
                  <Card className="stack" style={{ gap: "var(--sp-4)" }}>
                    <SectionHeadingInline icon={Target} title="Weekly activity" />
                    <WeeklyActivityChart activity={sections.weeklyActivity} />
                  </Card>
                  <Card className="stack" style={{ gap: "var(--sp-4)" }}>
                    <SectionHeadingInline icon={Flame} title="Coding streak" />
                    <StreakHeat streak={data.streak ?? {}} />
                  </Card>
                </div>
                <div className="dash-stack">
                  <Card className="stack" style={{ gap: "var(--sp-4)" }}>
                    <SectionHeadingInline icon={Sparkles} title="Weekly goal" />
                    <GoalRing goal={data.weekly_goal ?? {}} />
                  </Card>
                  <Card className="stack" style={{ gap: "var(--sp-4)" }}>
                    <SectionHeadingInline icon={CalendarDays} title="Upcoming events" />
                    <UpcomingEvents events={sections.upcomingEvents} />
                  </Card>
                  <Card className="stack" style={{ gap: "var(--sp-4)" }}>
                    <SectionHeadingInline icon={Medal} title="Recent badges" />
                    <EarnedBadges achievements={sections.achievements} />
                  </Card>
                </div>
              </div>
            </>
          )}

          <section aria-labelledby="dash-recommended">
            <SectionHeading
              eyebrow="Picked for you"
              title="Recommended courses"
              action={<Button variant="outline" to="/learning">All courses <ArrowRight size={16} /></Button>}
            />
            <span id="dash-recommended" className="sr-only">Recommended courses</span>
            <RecommendedCourses courses={sections.recommended} />
          </section>

          <div className="dash-grid">
            <section aria-labelledby="dash-community">
              <span id="dash-community" className="sr-only">Recent community activity</span>
              <SectionHeading eyebrow="Community" title="Latest activity" action={<Button variant="link" to="/community">Open community</Button>} />
              <CommunityActivity posts={sections.community} />
            </section>
            <section aria-labelledby="dash-quicklinks">
              <span id="dash-quicklinks" className="sr-only">Quick links</span>
              <SectionHeading eyebrow="Jump back in" title="Quick links" />
              <QuickLinks quickLinks={data.quick_links} />
            </section>
          </div>
        </>
      ) : null}
    </div>
  );
}

function SectionHeadingInline({ icon: Icon, title }) {
  return (
    <h2 style={{ display: "flex", alignItems: "center", gap: "var(--sp-2)", fontSize: "var(--fs-md)" }}>
      <Icon size={18} style={{ color: "var(--violet)" }} aria-hidden="true" />
      {title}
    </h2>
  );
}

function QuickLinks({ quickLinks }) {
  const pick = (key, fallback) => {
    const value = quickLinks?.[key];
    return typeof value === "string" && value.startsWith("/") ? value : fallback;
  };
  const links = [
    { to: pick("projects", "/community/projects"), label: "Project showcase", icon: Network },
    { to: pick("mentors", "/mentorship"), label: "Find a mentor", icon: Users },
    { to: pick("challenges", "/challenges"), label: "Coding challenges", icon: Code2 },
  ];
  return (
    <div className="stack" style={{ gap: "var(--sp-3)" }}>
      {links.map((link) => (
        <Button key={link.to} variant="outline" block to={link.to}>
          <link.icon size={17} aria-hidden="true" /> {link.label} <ArrowRight size={15} />
        </Button>
      ))}
    </div>
  );
}
