import { useState } from "react";
import { BadgeCheck, Pencil, ShieldX } from "lucide-react";
import { api } from "../../services/api";
import { useAsync, useDebouncedValue } from "../../hooks";
import { useToast } from "../../context/ToastContext";
import {
  Badge,
  Button,
  ConfirmDialog,
  EmptyState,
  ErrorState,
  IconButton,
  Modal,
  Pagination,
  SearchInput,
  Skeleton,
  TagInput,
  Tabs,
  UserCell,
} from "../../components/ui";
import { asList } from "../app/helpers";
import "./admin.css";

const STATUS_TABS = [
  { value: "all", label: "All" },
  { value: "pending", label: "Pending approval" },
  { value: "approved", label: "Approved" },
];

export default function AdminMentors() {
  const toast = useToast();
  const [status, setStatus] = useState("pending");
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const debounced = useDebouncedValue(search, 300);

  const isApprovedParam = status === "approved" ? "true" : status === "pending" ? "false" : undefined;

  const { data, loading, error, reload } = useAsync(
    (signal) => api.get("/admin/mentors/", { signal, params: { search: debounced || undefined, is_approved: isApprovedParam, page, page_size: 10 } }),
    [debounced, status, page]
  );

  const rows = asList(data);
  const count = data?.count ?? rows.length;
  const pageSize = data?.page_size ?? 10;

  const [editing, setEditing] = useState(null); // mentor row
  const [expertise, setExpertise] = useState([]);
  const [saving, setSaving] = useState(false);
  const [toUnapprove, setToUnapprove] = useState(null);
  const [busyId, setBusyId] = useState(null);

  const nameOf = (row) => row.display_name ?? row.user?.display_name ?? row.user?.username ?? row.email ?? "Mentor";

  const approve = async (row) => {
    setBusyId(row.id);
    try {
      await api.patch(`/admin/mentors/${row.id}/`, { is_approved: true });
      toast.success(`${nameOf(row)} approved.`);
      reload();
    } catch (err) {
      toast.error(err?.detail || "Approval failed.");
    } finally {
      setBusyId(null);
    }
  };

  const unapprove = async () => {
    if (!toUnapprove) return;
    setBusyId(toUnapprove.id);
    try {
      await api.patch(`/admin/mentors/${toUnapprove.id}/`, { is_approved: false });
      toast.success(`${nameOf(toUnapprove)} is no longer approved.`);
      setToUnapprove(null);
      reload();
    } catch (err) {
      toast.error(err?.detail || "Could not change approval status.");
    } finally {
      setBusyId(null);
    }
  };

  const openEdit = (row) => {
    setEditing(row);
    setExpertise(asList(row.expertise));
  };

  const saveExpertise = async () => {
    setSaving(true);
    try {
      await api.patch(`/admin/mentors/${editing.id}/`, { expertise });
      toast.success("Expertise updated.");
      setEditing(null);
      reload();
    } catch (err) {
      toast.error(err?.detail || "Could not save expertise.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="admin-panel">
      <div className="row" style={{ justifyContent: "space-between", alignItems: "center", flexWrap: "wrap" }}>
        <h2 style={{ fontSize: "var(--fs-lg)" }}>Mentor approval queue</h2>
        <span className="muted" style={{ fontSize: "var(--fs-sm)" }} aria-live="polite">
          {loading ? "Loading…" : `${count.toLocaleString()} mentor${count === 1 ? "" : "s"}`}
        </span>
      </div>

      <div className="admin-toolbar">
        <div className="admin-toolbar__grow">
          <SearchInput label="Search mentors" value={search} onChange={(value) => { setSearch(value); setPage(1); }} placeholder="Search by name…" />
        </div>
        <div className="field">
          <span className="field__label">Approval</span>
          <Tabs items={STATUS_TABS} value={status} onChange={(value) => { setStatus(value); setPage(1); }} ariaLabel="Mentor approval status" />
        </div>
      </div>

      {loading ? (
        <div className="stack" style={{ gap: 8 }}>
          {[0, 1, 2].map((key) => (
            <Skeleton key={key} style={{ height: 72 }} />
          ))}
        </div>
      ) : null}
      {!loading && error ? <ErrorState error={error} onRetry={reload} title="Could not load mentors" /> : null}
      {!loading && !error && rows.length === 0 ? (
        <EmptyState icon={BadgeCheck} title="Nothing in this queue" description="There are no mentors matching this filter right now." />
      ) : null}

      {!loading && !error && rows.length > 0 ? (
        <>
          <div className="table-wrap">
            <table className="table">
              <caption className="sr-only">Mentors with expertise and approval status.</caption>
              <thead>
                <tr>
                  <th scope="col">Mentor</th>
                  <th scope="col">Expertise</th>
                  <th scope="col">Status</th>
                  <th scope="col"><span className="sr-only">Actions</span></th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row, index) => (
                  <tr key={row.id ?? index}>
                    <td>
                      <UserCell
                        user={{ display_name: nameOf(row), email: row.email ?? row.user?.email, avatar: row.avatar ?? row.user?.avatar }}
                        to={`/members/${row.user?.id ?? row.id}`}
                        subtitle={row.email ?? row.user?.email}
                      />
                    </td>
                    <td>
                      <div className="row" style={{ gap: 6 }}>
                        {asList(row.expertise).length === 0 ? (
                          <span className="muted" style={{ fontSize: "var(--fs-xs)" }}>No expertise set</span>
                        ) : (
                          asList(row.expertise).slice(0, 4).map((tag) => (
                            <Badge key={tag} variant="neutral">{tag}</Badge>
                          ))
                        )}
                      </div>
                    </td>
                    <td>
                      <span className={`status-pill ${row.is_approved ? "status-pill--ok" : "status-pill--warn"}`}>
                        {row.is_approved ? "Approved" : "Pending"}
                      </span>
                    </td>
                    <td>
                      <div className="admin-cell__actions">
                        <IconButton label={`Edit expertise for ${nameOf(row)}`} variant="ghost" onClick={() => openEdit(row)}>
                          <Pencil size={15} />
                        </IconButton>
                        {row.is_approved ? (
                          <IconButton label={`Revoke approval for ${nameOf(row)}`} variant="ghost" onClick={() => setToUnapprove(row)}>
                            <ShieldX size={15} />
                          </IconButton>
                        ) : (
                          <Button size="sm" variant="outline" loading={busyId === row.id} onClick={() => approve(row)}>
                            <BadgeCheck size={15} aria-hidden="true" /> Approve
                          </Button>
                        )}
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
        open={Boolean(editing)}
        onClose={() => setEditing(null)}
        title={`Expertise — ${editing ? nameOf(editing) : ""}`}
        description="These topics power mentor matching. Add one per line."
        footer={
          <>
            <Button variant="ghost" onClick={() => setEditing(null)} disabled={saving}>Cancel</Button>
            <Button onClick={saveExpertise} loading={saving}>
              <BadgeCheck size={16} aria-hidden="true" /> Save expertise
            </Button>
          </>
        }
      >
        <TagInput label="Areas of expertise" value={expertise} onChange={setExpertise} placeholder="Add a topic and press Enter" />
      </Modal>

      <ConfirmDialog
        open={Boolean(toUnapprove)}
        onClose={() => setToUnapprove(null)}
        onConfirm={unapprove}
        busy={busyId === toUnapprove?.id}
        variant="danger"
        confirmLabel="Revoke approval"
        title="Revoke mentor approval?"
        message={`${toUnapprove ? nameOf(toUnapprove) : "This mentor"} will stop appearing in the public mentor directory. Existing matches are unaffected.`}
      />
    </div>
  );
}
