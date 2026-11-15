import { useMemo, useState } from "react";
import {
  BookOpen,
  BarChart3,
  FileWarning,
  Radio,
  Users as UsersIcon,
  Code2,
} from "lucide-react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useReducedMotion } from "framer-motion";
import { api, endpoints } from "../../services/api";
import { useAsync } from "../../hooks";
import { Card, ErrorState, Field, Select, Skeleton, Stat } from "../../components/ui";
import { num } from "../app/helpers";
import "./admin.css";

const LINE_COLOR = "#a855f7";

const METRICS = [
  { value: "signups", label: "New signups" },
  { value: "enrollments", label: "Course enrollments" },
  { value: "submissions", label: "Challenge submissions" },
  { value: "activity", label: "Daily activity" },
];

const RANGES = [
  { value: "7", label: "Last 7 days" },
  { value: "30", label: "Last 30 days" },
  { value: "90", label: "Last 90 days" },
];

// Overview counters are rendered straight from the API, which groups them by
// domain; a missing path becomes an em dash rather than a fabricated zero.
function OverviewStats({ data }) {
  const cells = [
    { key: "users", label: "Members", icon: UsersIcon, tone: "brand", path: (d) => d.users?.total },
    { key: "courses", label: "Courses", icon: BookOpen, tone: "cyan", path: (d) => d.learning?.courses },
    { key: "enrollments", label: "Enrollments", icon: Radio, tone: "success", path: (d) => d.learning?.enrollments },
    { key: "posts", label: "Community posts", icon: BarChart3, tone: "brand", path: (d) => d.community?.posts },
    { key: "reports", label: "Open reports", icon: FileWarning, tone: "warning", path: (d) => d.moderation?.reports_pending },
    { key: "submissions", label: "Submissions", icon: Code2, tone: "pink", path: (d) => d.challenges?.submissions },
  ];
  return (
    <div className="stat-grid">
      {cells.map((cell) => {
        const value = data ? cell.path(data) : null;
        return (
          <Stat
            key={cell.key}
            label={cell.label}
            icon={cell.icon}
            tone={cell.tone}
            value={value == null ? "—" : num(value).toLocaleString()}
          />
        );
      })}
    </div>
  );
}

function AnalyticsChart() {
  const reduce = useReducedMotion();
  const [metric, setMetric] = useState("signups");
  const [days, setDays] = useState("30");

  const { data, loading, error, reload } = useAsync(
    (signal) => api.get(endpoints.adminAnalytics, { signal, params: { metric, days } }),
    [metric, days]
  );

  const chartData = useMemo(() => {
    const labels = Array.isArray(data?.labels) ? data.labels : [];
    const rawSeries = data?.series;
    const values = Array.isArray(rawSeries)
      ? rawSeries.map((point) => (typeof point === "object" ? num(point.value ?? point.y ?? point.count) : num(point)))
      : [];
    return labels.map((label, index) => ({ label: String(label), value: values[index] ?? 0 }));
  }, [data]);

  const total = chartData.reduce((acc, point) => acc + point.value, 0);
  const metricLabel = METRICS.find((item) => item.value === metric)?.label ?? metric;
  const summary = `${metricLabel} over the last ${days} days. ${chartData.length} points, total ${total.toLocaleString()}.`;

  return (
    <Card className="stack" style={{ gap: "var(--sp-4)" }}>
      <div className="row" style={{ justifyContent: "space-between", alignItems: "flex-end", flexWrap: "wrap", gap: "var(--sp-4)" }}>
        <div>
          <span className="eyebrow">Analytics</span>
          <h2 style={{ fontSize: "var(--fs-lg)", marginTop: "var(--sp-2)" }}>Trends</h2>
        </div>
        <div className="admin-toolbar">
          <Field label="Metric" htmlFor="an-metric">
            <Select id="an-metric" options={METRICS} value={metric} onChange={(event) => setMetric(event.target.value)} />
          </Field>
          <Field label="Range" htmlFor="an-days">
            <Select id="an-days" options={RANGES} value={days} onChange={(event) => setDays(event.target.value)} />
          </Field>
        </div>
      </div>

      {loading ? <Skeleton style={{ height: 300 }} /> : null}
      {!loading && error ? <ErrorState error={error} onRetry={reload} title="Analytics unavailable" /> : null}
      {!loading && !error ? (
        <>
          <div className="chart-frame" role="img" aria-label={summary}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 8, right: 12, bottom: 0, left: -16 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,255,0.12)" vertical={false} />
                <XAxis dataKey="label" tick={{ fill: "#7e88ad", fontSize: 12 }} stroke="rgba(148,163,255,0.2)" minTickGap={16} />
                <YAxis tick={{ fill: "#7e88ad", fontSize: 12 }} stroke="rgba(148,163,255,0.2)" width={44} allowDecimals={false} />
                <Tooltip
                  contentStyle={{ background: "#131a33", border: "1px solid rgba(167,139,250,0.42)", borderRadius: 12, fontSize: 13 }}
                  labelStyle={{ color: "#f2f4ff" }}
                  formatter={(value) => [value, metricLabel]}
                />
                <Legend wrapperStyle={{ display: "none" }} />
                <Line type="monotone" dataKey="value" stroke={LINE_COLOR} strokeWidth={2.5} dot={false} isAnimationActive={!reduce} />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <details className="chart-fallback">
            <summary>View data as a table</summary>
            <div className="table-wrap" style={{ marginTop: "var(--sp-3)" }}>
              <table className="table">
                <caption className="sr-only">{`${metricLabel}, ${days}-day series`}</caption>
                <thead>
                  <tr>
                    <th scope="col">Period</th>
                    <th scope="col">{metricLabel}</th>
                  </tr>
                </thead>
                <tbody>
                  {chartData.map((point, index) => (
                    <tr key={`${point.label}-${index}`}>
                      <td>{point.label}</td>
                      <td>{point.value.toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </details>
        </>
      ) : null}
    </Card>
  );
}

export default function AdminOverview() {
  const { data, loading, error, reload } = useAsync((signal) => api.get(endpoints.adminOverview, { signal }), []);

  return (
    <div className="admin-panel">
      <div className="readonly-note" role="note">
        <BarChart3 size={16} aria-hidden="true" /> Overview and analytics are read-only — every number is computed by the API.
      </div>

      {loading ? (
        <div className="stat-grid">
          {[0, 1, 2, 3, 4, 5].map((key) => (
            <Skeleton key={key} style={{ height: 110 }} />
          ))}
        </div>
      ) : null}

      {!loading && error ? (
        <ErrorState error={error} onRetry={reload} title="Could not load the overview" />
      ) : null}

      {!loading && !error && data ? <OverviewStats data={data} /> : null}

      <AnalyticsChart />
    </div>
  );
}
