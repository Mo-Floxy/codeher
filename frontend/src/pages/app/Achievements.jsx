import { useEffect, useMemo, useState } from "react";
import {
  Award,
  Crown,
  Flame,
  Lock,
  Medal,
  Sparkles,
  Star,
  Target,
  Trophy,
} from "lucide-react";
import { api } from "../../services/api";
import { useAsync } from "../../hooks";
import { useAuth } from "../../context/AuthContext";
import { useToast } from "../../context/ToastContext";
import {
  Avatar,
  Badge,
  Button,
  Card,
  EmptyState,
  ErrorState,
  Field,
  Input,
  ProgressBar,
  SectionHeading,
  Skeleton,
  Stat,
  Tabs,
} from "../../components/ui";
import { asList, num } from "./helpers";
import "./app.css";

const PERIODS = [
  { value: "weekly", label: "This week" },
  { value: "alltime", label: "All time" },
];
const SCOPES = [
  { value: "xp", label: "XP" },
  { value: "streak", label: "Streak" },
];

const MEDAL_COLORS = { 1: "#fbbf24", 2: "#c7d2fe", 3: "#f9a8d4" };

function requirementOf(item) {
  return item.requirement ?? item.requirement_text ?? item.criteria ?? item.description ?? "Keep learning to unlock this badge.";
}

function valueOf(row, scope) {
  if (scope === "streak") {
    return num(row.streak ?? row.current_streak ?? row.value ?? row.points);
  }
  return num(row.xp ?? row.total_xp ?? row.points ?? row.value);
}

function isSameUser(row, userId) {
  if (userId == null || !row) return false;
  const rowUserId = row.user?.id ?? row.user ?? row.id;
  return String(rowUserId) === String(userId);
}

function LeaderboardRow({ row, scope, pinned }) {
  const displayName = row.display_name ?? row.user?.display_name ?? row.user?.username ?? "Member";
  const avatarUser = row.avatar ? { display_name: displayName, avatar: row.avatar } : row.user ?? { display_name: displayName };
  const rank = num(row.rank);
  const unit = scope === "streak" ? "day streak" : "XP";
  return (
    <div className={`lb-row ${pinned ? "lb-row--me" : ""}`}>
      <div className="lb-row__rank" aria-label={`Rank ${rank}`}>
        {rank >= 1 && rank <= 3 ? (
          <span className="lb-medal" style={{ background: MEDAL_COLORS[rank], color: "#0a0e1f" }}>
            {rank === 1 ? <Crown size={16} aria-hidden="true" /> : rank}
          </span>
        ) : (
          rank || "–"
        )}
      </div>
      <div style={{ minWidth: 0 }}>
        <span className="row" style={{ gap: "var(--sp-2)" }}>
          <Avatar user={avatarUser} size="sm" />
          <span style={{ fontWeight: 700, color: "var(--text-primary)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {displayName}
          </span>
          {pinned && <Badge variant="brand">You</Badge>}
        </span>
      </div>
      <span className="lb-value">{valueOf(row, scope).toLocaleString()} <span className="muted" style={{ fontWeight: 600 }}>{unit}</span></span>
    </div>
  );
}

function BadgeTile({ item, locked }) {
  return (
    <div className={`badge-tile ${locked ? "badge-tile--locked" : ""}`}>
      <span className="badge-tile__icon">
        {locked ? <Lock size={20} aria-hidden="true" /> : <Medal size={20} aria-hidden="true" />}
      </span>
      <span className="badge-tile__title">{item.title || item.badge || "Badge"}</span>
      {locked ? (
        <p className="muted" style={{ fontSize: "var(--fs-sm)" }}>{requirementOf(item)}</p>
      ) : (
        <>
          <p className="muted" style={{ fontSize: "var(--fs-sm)" }}>{item.description || requirementOf(item)}</p>
          <span style={{ fontSize: "var(--fs-xs)", color: "var(--success)" }}>
            {item.earned_at ? `Earned ${new Date(item.earned_at).toLocaleDateString()}` : "Earned"}
          </span>
        </>
      )}
    </div>
  );
}

function GoalEditor() {
  const { data, loading, error, reload, setData } = useAsync((signal) => api.get("/achievements/me/goals/", { signal }), []);
  const toast = useToast();
  const [draft, setDraft] = useState("");
  const [fieldError, setFieldError] = useState("");
  const [saving, setSaving] = useState(false);

  const target = data ? num(data.weekly_goal_minutes ?? data.target_minutes) : null;

  useEffect(() => {
    if (data) setDraft(String(num(data.weekly_goal_minutes ?? data.target_minutes)));
  }, [data]);

  const validate = (raw) => {
    if (raw.trim() === "") return "Enter a value in minutes.";
    if (!/^\d+$/.test(raw.trim())) return "Use a whole number of minutes.";
    const value = Number(raw);
    if (value < 0) return "Minutes cannot be negative.";
    if (value > 10080) return "That is more minutes than there are in a week.";
    return "";
  };

  const onChange = (event) => {
    const raw = event.target.value;
    setDraft(raw);
    setFieldError(validate(raw));
  };

  const save = async (event) => {
    event.preventDefault();
    const message = validate(draft);
    setFieldError(message);
    if (message) return;
    setSaving(true);
    try {
      const updated = await api.patch("/achievements/me/goals/", { weekly_goal_minutes: Number(draft) });
      setData(updated ?? data);
      toast.success("Weekly goal updated.");
      reload();
    } catch (err) {
      toast.error(err.messageFor ? err.messageFor("weekly_goal_minutes") : "Could not save your goal.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Card className="stack" style={{ gap: "var(--sp-4)" }}>
      <SectionHeadingInline icon={Target} title="Weekly goal" />
      {loading ? <Skeleton style={{ height: 80 }} /> : null}
      {!loading && error ? <ErrorState error={error} onRetry={reload} title="Goal unavailable" /> : null}
      {!loading && data ? (
        <form className="stack" style={{ gap: "var(--sp-3)" }} onSubmit={save} noValidate>
          <Field
            label="Target minutes per week"
            hint="Set how long you want to study each week — the dashboard ring tracks it."
            error={fieldError}
            htmlFor="goal-minutes"
          >
            <Input
              id="goal-minutes"
              inputMode="numeric"
              value={draft}
              onChange={onChange}
              error={fieldError}
            />
          </Field>
          <div aria-live="polite">
            <ProgressBar value={num(data.percent ?? (num(data.actual_minutes) / Math.max(1, target)) * 100)} label="This week" variant="success" />
            <p className="muted" style={{ fontSize: "var(--fs-xs)", marginTop: 6 }}>
              {num(data.actual_minutes)} of {target} minutes logged this week.
            </p>
          </div>
          <Button type="submit" loading={saving} disabled={fieldError !== ""}>
            <Sparkles size={16} aria-hidden="true" /> Save goal
          </Button>
        </form>
      ) : null}
    </Card>
  );
}

function LevelsTable() {
  const { data, loading, error, reload } = useAsync((signal) => api.get("/achievements/me/levels/", { signal }), []);

  const levels = useMemo(() => {
    const raw = data?.levels ?? asList(data);
    return Array.isArray(raw) ? raw : [];
  }, [data]);
  const currentLevel = num(data?.current_level ?? data?.level);

  return (
    <Card flush className="stack" style={{ gap: 0 }}>
      <div style={{ padding: "var(--sp-5)" }}>
        <SectionHeadingInline icon={Crown} title="Level path" />
      </div>
      {loading ? <div style={{ padding: "0 var(--sp-5) var(--sp-5)" }}><Skeleton style={{ height: 200 }} /></div> : null}
      {!loading && error ? <div style={{ padding: "0 var(--sp-5) var(--sp-5)" }}><ErrorState error={error} onRetry={reload} title="Levels unavailable" /></div> : null}
      {!loading && !error && levels.length === 0 ? (
        <div style={{ padding: "0 var(--sp-5) var(--sp-5)" }}>
          <EmptyState icon={Crown} title="No level table yet" description="Levels unlock as the gamification system seeds its thresholds." />
        </div>
      ) : null}
      {!loading && !error && levels.length > 0 ? (
        <div className="table-wrap" style={{ borderTop: "1px solid var(--glass-border)" }}>
          <table className="table">
            <caption className="sr-only">XP thresholds for each level; your current level is highlighted.</caption>
            <thead>
              <tr>
                <th scope="col">Level</th>
                <th scope="col">Title</th>
                <th scope="col">XP required</th>
              </tr>
            </thead>
            <tbody>
              {levels.map((row, index) => {
                const levelNumber = num(row.level ?? index + 1);
                const isCurrent = levelNumber === currentLevel;
                return (
                  <tr key={row.level ?? index} style={isCurrent ? { background: "var(--purple-soft)" } : undefined}>
                    <td>
                      <span style={{ fontWeight: 800 }}>{levelNumber}</span>
                      {isCurrent && <Badge variant="brand" className="" >You are here</Badge>}
                    </td>
                    <td>{row.title ?? row.name ?? `Level ${levelNumber}`}</td>
                    <td>{num(row.min_xp ?? row.xp_threshold ?? row.xp_required ?? row.threshold).toLocaleString()}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : null}
    </Card>
  );
}

function Leaderboard() {
  const { user } = useAuth();
  const [period, setPeriod] = useState("weekly");
  const [scope, setScope] = useState("xp");
  const { data, loading, error, reload } = useAsync(
    (signal) => api.get("/achievements/leaderboard/", { signal, params: { period, scope } }),
    [period, scope]
  );

  const rows = useMemo(() => asList(data), [data]);
  const me = useMemo(
    () => data?.me ?? data?.current_user ?? rows.find((row) => isSameUser(row, user?.id)) ?? null,
    [data, rows, user?.id]
  );

  return (
    <Card className="stack" style={{ gap: "var(--sp-4)" }}>
      <SectionHeadingInline icon={Trophy} title="Leaderboard" />
      <div className="stack" style={{ gap: "var(--sp-3)" }}>
        <Tabs items={PERIODS} value={period} onChange={setPeriod} ariaLabel="Leaderboard period" />
        <Tabs items={SCOPES} value={scope} onChange={setScope} ariaLabel="Leaderboard measure" />
      </div>

      {loading ? (
        <div className="stack" style={{ gap: 6 }}>
          {[0, 1, 2, 3, 4].map((key) => (
            <Skeleton key={key} style={{ height: 48 }} />
          ))}
        </div>
      ) : null}
      {!loading && error ? <ErrorState error={error} onRetry={reload} title="Leaderboard unavailable" /> : null}
      {!loading && !error && rows.length === 0 ? (
        <EmptyState icon={Trophy} title="No rankings yet" description="The leaderboard fills up once members start earning XP and streaks in this period." />
      ) : null}
      {!loading && !error && rows.length > 0 ? (
        <div aria-live="polite">
          {rows.map((row, index) => (
            <LeaderboardRow key={row.user?.id ?? row.id ?? index} row={row} scope={scope} pinned={false} />
          ))}
          {me && !rows.some((row) => isSameUser(row, user?.id)) ? <LeaderboardRow row={{ ...me, rank: me.rank ?? 0 }} scope={scope} pinned /> : null}
        </div>
      ) : null}
    </Card>
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

export default function Achievements() {
  const catalogue = useAsync((signal) => api.get("/achievements/", { signal }), []);

  const badges = useMemo(() => asList(catalogue.data), [catalogue.data]);
  const earned = useMemo(() => badges.filter((item) => item.is_earned || item.earned), [badges]);
  const locked = useMemo(() => badges.filter((item) => !(item.is_earned || item.earned)), [badges]);
  const total = badges.length;

  return (
    <div className="app-page">
      <header className="app-page__head">
        <h1 className="app-page__title">Achievements</h1>
        <p className="app-page__sub">Every badge, level and ranking here is earned from real activity recorded by the server.</p>
      </header>

      {catalogue.loading ? (
        <Skeleton style={{ height: 90 }} />
      ) : catalogue.error ? (
        <ErrorState error={catalogue.error} onRetry={catalogue.reload} title="Badges unavailable" />
      ) : (
        <div className="stat-grid">
          <Stat label="Badges earned" value={earned.length} icon={Award} tone="brand" />
          <Stat label="Still to unlock" value={locked.length} icon={Lock} tone="warning" />
          <Stat label="Catalogue total" value={total} icon={Star} tone="cyan" delta={total ? `${Math.round((earned.length / total) * 100)}% complete` : undefined} />
        </div>
      )}

      {catalogue.loading ? <Skeleton style={{ height: 240 }} /> : null}

      {catalogue.data ? (
        <>
          <section aria-labelledby="ach-earned">
            <span id="ach-earned" className="sr-only">Earned badges</span>
            <SectionHeading eyebrow="Earned" title={`Your badges (${earned.length})`} />
            {earned.length === 0 ? (
              <EmptyState
                icon={Award}
                title="No badges yet"
                description="Complete a lesson, pass a quiz, or solve a challenge to earn your first badge."
                action={<Button variant="ghost" to="/challenges">Try a challenge</Button>}
              />
            ) : (
              <div className="badge-grid">
                {earned.map((item, index) => (
                  <BadgeTile key={item.badge ?? item.id ?? index} item={item} locked={false} />
                ))}
              </div>
            )}
          </section>

          <section aria-labelledby="ach-locked">
            <span id="ach-locked" className="sr-only">Locked badges</span>
            <SectionHeading eyebrow="Locked" title={`Coming up (${locked.length})`} description="Requirements only — we never show progress on a badge you haven't started." />
            {locked.length === 0 ? (
              <p className="muted">You have unlocked every badge in the catalogue. </p>
            ) : (
              <div className="badge-grid">
                {locked.map((item, index) => (
                  <BadgeTile key={item.badge ?? item.id ?? index} item={item} locked />
                ))}
              </div>
            )}
          </section>
        </>
      ) : null}

      <div className="dash-grid">
        <div className="dash-stack">
          <LevelsTable />
          <Leaderboard />
        </div>
        <div className="dash-stack">
          <GoalEditor />
          <Card className="stack" style={{ gap: "var(--sp-3)" }}>
            <SectionHeadingInline icon={Flame} title="Keep going" />
            <p className="muted" style={{ fontSize: "var(--fs-sm)" }}>
              Badges and XP update automatically as the server records verified actions.
            </p>
            <Button variant="outline" to="/learning">
              <Sparkles size={16} aria-hidden="true" /> Continue learning
            </Button>
            <Button variant="link" to="/dashboard">
              Back to dashboard
            </Button>
          </Card>
        </div>
      </div>
    </div>
  );
}
