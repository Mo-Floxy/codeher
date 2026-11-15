import { useMemo, useState } from "react";
import { Gavel, ShieldAlert, Trash, Eye } from "lucide-react";
import { api, endpoints } from "../../services/api";
import { useAsync } from "../../hooks";
import { useToast } from "../../context/ToastContext";
import {
  Badge,
  Button,
  EmptyState,
  ErrorState,
  Field,
  Modal,
  Pagination,
  Select,
  Skeleton,
  Tabs,
  Textarea,
  UserCell,
} from "../../components/ui";
import { asList, formatDate } from "../app/helpers";
import "./admin.css";

const STATUS_TABS = [
  { value: "pending", label: "Pending" },
  { value: "resolved", label: "Resolved" },
];

const ACTIONS = [
  { value: "dismiss", label: "Dismiss report (keep content)" },
  { value: "remove_content", label: "Remove the reported content" },
];

function previewOf(report) {
  const content = report.content ?? {};
  return (
    report.content_preview ??
    content.title ??
    report.post?.title ??
    report.project?.title ??
    (report.object_type ? `${report.object_type} #${report.object_id}` : "Reported content")
  );
}

function kindOf(report) {
  const type = String(report.content_type ?? report.object_type ?? "").toLowerCase();
  if (type.includes("project")) return "Project";
  if (type.includes("post")) return "Post";
  return type || "Content";
}

function reporterName(report) {
  const r = report.reporter ?? report.reported_by ?? report.user;
  return r?.display_name ?? r?.username ?? "A member";
}

export default function AdminModeration() {
  const toast = useToast();
  const [status, setStatus] = useState("pending");
  const [page, setPage] = useState(1);

  const { data, loading, error, reload } = useAsync(
    (signal) => api.get(endpoints.adminReports, { signal, params: { status, page, page_size: 10 } }),
    [status, page]
  );

  const rows = useMemo(() => asList(data), [data]);
  const count = data?.count ?? rows.length;
  const pageSize = data?.page_size ?? 10;

  const [target, setTarget] = useState(null);
  const [action, setAction] = useState("dismiss");
  const [note, setNote] = useState("");
  const [saving, setSaving] = useState(false);

  const openResolve = (report) => {
    setTarget(report);
    setAction("dismiss");
    setNote("");
  };

  const resolve = async () => {
    if (!target) return;
    setSaving(true);
    try {
      await api.post(`/admin/reports/${target.id}/resolve/`, { action, note: note.trim() || undefined });
      toast.success(action === "remove_content" ? "Content removed and report resolved." : "Report dismissed.");
      setTarget(null);
      reload();
    } catch (err) {
      toast.error(err?.detail || "Could not resolve this report.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="admin-panel">
      <div className="row" style={{ justifyContent: "space-between", alignItems: "center", flexWrap: "wrap" }}>
        <h2 style={{ fontSize: "var(--fs-lg)" }}>Content reports</h2>
        <span className="muted" style={{ fontSize: "var(--fs-sm)" }} aria-live="polite">
          {loading ? "Loading…" : `${count.toLocaleString()} report${count === 1 ? "" : "s"}`}
        </span>
      </div>

      <Tabs
        items={STATUS_TABS}
        value={status}
        onChange={(value) => { setStatus(value); setPage(1); }}
        ariaLabel="Report status"
      />

      {loading ? (
        <div className="stack" style={{ gap: 8 }}>
          {[0, 1, 2].map((key) => (
            <Skeleton key={key} style={{ height: 72 }} />
          ))}
        </div>
      ) : null}
      {!loading && error ? <ErrorState error={error} onRetry={reload} title="Could not load reports" /> : null}
      {!loading && !error && rows.length === 0 ? (
        <EmptyState
          icon={status === "pending" ? ShieldAlert : Eye}
          title={status === "pending" ? "No pending reports" : "No resolved reports"}
          description={status === "pending" ? "Nothing is waiting for moderation — the queue is clear." : "Resolved reports will be listed here."}
        />
      ) : null}

      {!loading && !error && rows.length > 0 ? (
        <>
          <div className="table-wrap">
            <table className="table">
              <caption className="sr-only">Flagged posts and projects reported by members.</caption>
              <thead>
                <tr>
                  <th scope="col">Content</th>
                  <th scope="col">Reporter</th>
                  <th scope="col">Reason</th>
                  <th scope="col">Details</th>
                  <th scope="col">Status</th>
                  <th scope="col"><span className="sr-only">Actions</span></th>
                </tr>
              </thead>
              <tbody>
                {rows.map((report, index) => (
                  <tr key={report.id ?? index}>
                    <td>
                      <span className="row" style={{ gap: "var(--sp-2)", alignItems: "flex-start" }}>
                        <Badge variant="neutral">{kindOf(report)}</Badge>
                        <span style={{ minWidth: 0 }}>
                          <span style={{ display: "block", fontWeight: 700, color: "var(--text-primary)" }}>{previewOf(report)}</span>
                          {report.created_at ? <span className="muted" style={{ fontSize: "var(--fs-xs)" }}>{formatDate(report.created_at)}</span> : null}
                        </span>
                      </span>
                    </td>
                    <td>
                      <UserCell user={{ display_name: reporterName(report), avatar: report.reporter?.avatar }} />
                    </td>
                    <td>{report.reason ?? "—"}</td>
                    <td style={{ maxWidth: "30ch" }}>{report.details ?? report.comment ?? <span className="muted">—</span>}</td>
                    <td>
                      <span className={`status-pill ${report.status === "resolved" ? "status-pill--ok" : "status-pill--warn"}`}>
                        {report.status === "resolved" ? "Resolved" : "Pending"}
                      </span>
                      {report.resolution ? (
                        <span className="muted" style={{ fontSize: "var(--fs-xs)", display: "block", marginTop: 4 }}>
                          {report.resolution}
                        </span>
                      ) : null}
                    </td>
                    <td>
                      <div className="admin-cell__actions">
                        <Button size="sm" variant={report.status === "resolved" ? "ghost" : "outline"} onClick={() => openResolve(report)} disabled={report.status === "resolved"}>
                          <Gavel size={15} aria-hidden="true" /> {report.status === "resolved" ? "Resolved" : "Resolve"}
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination count={count} page={page} pageSize={pageSize} onPageChange={setPage} />
        </>
      ) : null}

      <Modal
        open={Boolean(target)}
        onClose={() => setTarget(null)}
        title="Resolve report"
        description={`Action for the reported ${target ? kindOf(target).toLowerCase() : "content"}. This is recorded against the report.`}
        footer={
          <>
            <Button variant="ghost" onClick={() => setTarget(null)} disabled={saving}>Cancel</Button>
            <Button variant={action === "remove_content" ? "danger" : "primary"} onClick={resolve} loading={saving}>
              {action === "remove_content" ? <Trash size={16} aria-hidden="true" /> : <Eye size={16} aria-hidden="true" />}
              {action === "remove_content" ? "Remove & resolve" : "Dismiss & resolve"}
            </Button>
          </>
        }
      >
        <div className="admin-modal-form">
          <Field label="Action" htmlFor="report-action">
            <Select id="report-action" options={ACTIONS} value={action} onChange={(event) => setAction(event.target.value)} />
          </Field>
          <Field label="Moderator note" hint="Optional — saved with the resolution for the audit trail." htmlFor="report-note">
            <Textarea id="report-note" value={note} onChange={(event) => setNote(event.target.value)} rows={3} placeholder="Why you took this action…" />
          </Field>
        </div>
      </Modal>
    </div>
  );
}
