import { useMemo, useState } from "react";
import { Megaphone, Plus, Trash2 } from "lucide-react";
import { api } from "../../services/api";
import { useAsync } from "../../hooks";
import { useToast } from "../../context/ToastContext";
import {
  Alert,
  Badge,
  Button,
  ConfirmDialog,
  EmptyState,
  ErrorState,
  Field,
  IconButton,
  Input,
  Modal,
  Pagination,
  Select,
  Skeleton,
  Textarea,
} from "../../components/ui";
import { asList, formatDate, num } from "../app/helpers";
import "./admin.css";

function recipientsOf(payload) {
  const value =
    payload?.recipients_count ??
    payload?.recipient_count ??
    payload?.sent_count ??
    payload?.audience_size ??
    payload?.recipients;
  return typeof value === "number" ? value : value != null && !Number.isNaN(Number(value)) ? Number(value) : null;
}

export default function AdminAnnouncements() {
  const toast = useToast();
  const [page, setPage] = useState(1);

  const list = useAsync((signal) => api.get("/admin/announcements/", { signal, params: { page, page_size: 10 } }), [page]);
  const courses = useAsync((signal) => api.get("/admin/courses/", { signal, params: { page_size: 50 } }), []);

  const rows = useMemo(() => asList(list.data), [list.data]);
  const count = list.data?.count ?? rows.length;
  const pageSize = list.data?.page_size ?? 10;

  const courseOptions = useMemo(
    () => [{ value: "", label: "Whole platform" }, ...asList(courses.data).map((course) => ({ value: course.id, label: course.title ?? `#${course.id}` }))],
    [courses.data]
  );

  const [modal, setModal] = useState({ open: false, row: null });
  const [form, setForm] = useState({ title: "", message: "", course: "" });
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);
  const [lastSent, setLastSent] = useState(null);
  const [toDelete, setToDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);

  const openNew = () => {
    setForm({ title: "", message: "", course: "" });
    setErrors({});
    setModal({ open: true, row: null });
  };
  const closeModal = () => setModal({ open: false, row: null });

  const validate = () => {
    const next = {};
    if (!form.title.trim()) next.title = "A title is required.";
    if (!form.message.trim()) next.message = "Write the announcement message.";
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const create = async () => {
    if (!validate()) return;
    setSaving(true);
    try {
      const result = await api.post("/admin/announcements/", {
        title: form.title.trim(),
        message: form.message.trim(),
        course: form.course || undefined,
      });
      const recipients = recipientsOf(result);
      setLastSent({ title: form.title.trim(), recipients });
      toast.success(recipients != null ? `Announcement queued for ${recipients.toLocaleString()} member${recipients === 1 ? "" : "s"}.` : "Announcement sent.");
      closeModal();
      list.reload();
    } catch (err) {
      setErrors(err?.fieldErrors ?? {});
      toast.error(err?.detail || "Could not send the announcement.");
    } finally {
      setSaving(false);
    }
  };

  const remove = async () => {
    if (!toDelete) return;
    setDeleting(true);
    try {
      await api.del(`/admin/announcements/${toDelete.id}/`);
      toast.success("Announcement deleted.");
      setToDelete(null);
      list.reload();
    } catch (err) {
      toast.error(err?.detail || "Could not delete the announcement.");
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="admin-panel">
      <div className="row" style={{ justifyContent: "space-between", alignItems: "center", flexWrap: "wrap" }}>
        <h2 style={{ fontSize: "var(--fs-lg)" }}>Announcements</h2>
        <Button size="sm" onClick={openNew}>
          <Plus size={15} aria-hidden="true" /> New announcement
        </Button>
      </div>

      <p className="muted" style={{ fontSize: "var(--fs-sm)" }}>
        Broadcasts are delivered as <code>course_announcement</code> notifications to enrolled members of the chosen course (or everyone if none is selected).
      </p>

      {lastSent ? (
        <Alert variant="success" title="Announcement created" onDismiss={() => setLastSent(null)}>
          “{lastSent.title}” will notify{" "}
          <strong>{lastSent.recipients != null ? `${lastSent.recipients.toLocaleString()} member${lastSent.recipients === 1 ? "" : "s"}` : "the audience"}</strong>.
          <span className="muted" style={{ fontSize: "var(--fs-xs)" }}> Recipient count is returned by the API.</span>
        </Alert>
      ) : null}

      {list.loading ? <Skeleton style={{ height: 200 }} /> : null}
      {!list.loading && list.error ? <ErrorState error={list.error} onRetry={list.reload} title="Could not load announcements" /> : null}
      {!list.loading && !list.error && rows.length === 0 ? (
        <EmptyState icon={Megaphone} title="No announcements yet" description="Send your first broadcast to course members." action={<Button onClick={openNew}>New announcement</Button>} />
      ) : null}

      {!list.loading && !list.error && rows.length > 0 ? (
        <>
          <div className="table-wrap">
            <table className="table">
              <caption className="sr-only">Announcements sent to members.</caption>
              <thead>
                <tr>
                  <th scope="col">Title</th>
                  <th scope="col">Audience</th>
                  <th scope="col">Sent</th>
                  <th scope="col">Recipients</th>
                  <th scope="col"><span className="sr-only">Actions</span></th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row, index) => (
                  <tr key={row.id ?? index}>
                    <td>
                      <span style={{ fontWeight: 700, color: "var(--text-primary)" }}>{row.title}</span>
                      {row.message ? <span className="muted" style={{ display: "block", fontSize: "var(--fs-xs)" }}>{row.message}</span> : null}
                    </td>
                    <td>
                      {row.course && typeof row.course === "object" ? (
                        <Badge variant="neutral">{row.course.title ?? `Course #${row.course.id}`}</Badge>
                      ) : (
                        <Badge variant="brand">{row.course ? `Course #${row.course}` : "Everyone"}</Badge>
                      )}
                    </td>
                    <td>{formatDate(row.created_at)}</td>
                    <td>{recipientsOf(row) != null ? num(recipientsOf(row)).toLocaleString() : "—"}</td>
                    <td>
                      <div className="admin-cell__actions">
                        <IconButton label={`Delete ${row.title}`} variant="ghost" onClick={() => setToDelete(row)}>
                          <Trash2 size={15} />
                        </IconButton>
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
        open={modal.open}
        onClose={closeModal}
        title="New announcement"
        description="Compose a broadcast. The API reports how many members will receive it."
        footer={
          <>
            <Button variant="ghost" onClick={closeModal} disabled={saving}>Cancel</Button>
            <Button onClick={create} loading={saving}>
              <Megaphone size={16} aria-hidden="true" /> Send announcement
            </Button>
          </>
        }
      >
        <div className="admin-modal-form">
          <Field label="Title" error={errors.title?.[0]} required htmlFor="ann-title">
            <Input id="ann-title" value={form.title} onChange={(event) => setForm((c) => ({ ...c, title: event.target.value }))} error={errors.title?.[0]} data-autofocus />
          </Field>
          <Field label="Target course" hint="Choose a course to notify its enrolled members, or leave on “Whole platform”." error={errors.course?.[0]} htmlFor="ann-course">
            <Select id="ann-course" options={courseOptions} value={form.course} onChange={(event) => setForm((c) => ({ ...c, course: event.target.value }))} />
          </Field>
          <Field label="Message" error={errors.message?.[0]} required htmlFor="ann-message">
            <Textarea id="ann-message" value={form.message} onChange={(event) => setForm((c) => ({ ...c, message: event.target.value }))} rows={4} error={errors.message?.[0]} />
          </Field>
        </div>
      </Modal>

      <ConfirmDialog
        open={Boolean(toDelete)}
        onClose={() => setToDelete(null)}
        onConfirm={remove}
        busy={deleting}
        variant="danger"
        confirmLabel="Delete"
        title="Delete this announcement?"
        message={`“${toDelete?.title ?? ""}” will be removed from the list. Already-delivered notifications are not recalled.`}
      />
    </div>
  );
}
