import { useState } from "react";
import { MoreVertical, ShieldCheck, UserCheck, UserX } from "lucide-react";
import { api, endpoints } from "../../services/api";
import { useAsync, useDebouncedValue } from "../../hooks";
import { useToast } from "../../context/ToastContext";
import {
  ConfirmDialog,
  Dropdown,
  DropdownItem,
  ErrorState,
  Field,
  IconButton,
  Pagination,
  SearchInput,
  Select,
  Skeleton,
  Tabs,
  UserCell,
} from "../../components/ui";
import { asList, formatDate, num } from "../app/helpers";
import "./admin.css";

const ROLE_OPTIONS = [
  { value: "", label: "All roles" },
  { value: "learner", label: "Learners" },
  { value: "mentor", label: "Mentors" },
  { value: "admin", label: "Admins" },
];

const STATUS_TABS = [
  { value: "", label: "All" },
  { value: "true", label: "Active" },
  { value: "false", label: "Inactive" },
];

const ALL_ROLES = ["learner", "mentor", "admin"];

function xpOf(user) {
  return num(user.total_xp ?? user.xp ?? user.profile?.total_xp);
}
function streakOf(user) {
  return num(user.current_streak ?? user.streak ?? user.profile?.current_streak);
}

export default function AdminUsers() {
  const toast = useToast();
  const [search, setSearch] = useState("");
  const [role, setRole] = useState("");
  const [isActive, setIsActive] = useState("");
  const [page, setPage] = useState(1);
  const debouncedSearch = useDebouncedValue(search, 350);

  const { data, loading, error, reload } = useAsync(
    (signal) =>
      api.get(endpoints.adminUsers, {
        signal,
        params: {
          search: debouncedSearch || undefined,
          role: role || undefined,
          is_active: isActive || undefined,
          page,
        },
      }),
    [debouncedSearch, role, isActive, page]
  );

  const rows = asList(data);
  const count = data?.count ?? rows.length;
  const pageSize = data?.page_size ?? 20;

  const [pending, setPending] = useState(null); // { user, type, value }
  const [busy, setBusy] = useState(false);

  const openRole = (user, nextRole) => setPending({ user, type: "role", value: nextRole });
  const openActive = (user, nextActive) => setPending({ user, type: "active", value: nextActive });

  const confirm = async () => {
    if (!pending) return;
    setBusy(true);
    const label = pending.user.display_name || pending.user.email || `#${pending.user.id}`;
    try {
      const body = pending.type === "role" ? { role: pending.value } : { is_active: pending.value };
      await api.patch(`/admin/users/${pending.user.id}/`, body);
      toast.success(
        pending.type === "role"
          ? `${label} is now a ${pending.value}.`
          : `${label} ${pending.value ? "reactivated" : "deactivated"}.`
      );
      setPending(null);
      reload();
    } catch (err) {
      toast.error(err?.detail || "That change could not be saved.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="admin-panel">
      <div className="row" style={{ justifyContent: "space-between", alignItems: "center", flexWrap: "wrap" }}>
        <h2 style={{ fontSize: "var(--fs-lg)" }}>Members</h2>
        <span className="muted" style={{ fontSize: "var(--fs-sm)" }} aria-live="polite">
          {loading ? "Loading…" : `${count.toLocaleString()} member${count === 1 ? "" : "s"}`}
        </span>
      </div>

      <div className="admin-toolbar">
        <div className="admin-toolbar__grow">
          <SearchInput label="Search members" value={search} onChange={(value) => { setSearch(value); setPage(1); }} placeholder="Email or name…" />
        </div>
        <Field label="Role" htmlFor="filter-role">
          <Select id="filter-role" options={ROLE_OPTIONS} value={role} onChange={(event) => { setRole(event.target.value); setPage(1); }} />
        </Field>
        <div className="field admin-toolbar__status">
          <span className="field__label">Status</span>
          <Tabs items={STATUS_TABS} value={isActive} onChange={(value) => { setIsActive(value); setPage(1); }} ariaLabel="Active status" />
        </div>
      </div>

      {loading ? (
        <div className="stack" style={{ gap: 8 }}>
          {[0, 1, 2, 3].map((key) => (
            <Skeleton key={key} style={{ height: 56 }} />
          ))}
        </div>
      ) : null}

      {!loading && error ? <ErrorState error={error} onRetry={reload} title="Could not load members" /> : null}

      {!loading && !error && rows.length === 0 ? (
        <div className="admin-empty">No members match these filters.</div>
      ) : null}

      {!loading && !error && rows.length > 0 ? (
        <>
          <div className="table-wrap">
            <table className="table">
              <caption className="sr-only">Platform members with roles, XP, streak, join date and status.</caption>
              <thead>
                <tr>
                  <th scope="col">Member</th>
                  <th scope="col">Role</th>
                  <th scope="col">XP</th>
                  <th scope="col">Streak</th>
                  <th scope="col">Joined</th>
                  <th scope="col">Status</th>
                  <th scope="col">
                    <span className="sr-only">Actions</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {rows.map((user, index) => (
                  <tr key={user.id ?? index}>
                    <td>
                      <UserCell
                        user={{ display_name: user.display_name || user.username, email: user.email, avatar: user.avatar }}
                        to={`/members/${user.id}`}
                        subtitle={user.email}
                      />
                    </td>
                    <td>
                      <span style={{ textTransform: "capitalize" }}>{user.role}</span>
                      {user.is_staff ? <span className="muted" style={{ fontSize: "var(--fs-xs)" }}> · staff</span> : null}
                    </td>
                    <td>{xpOf(user).toLocaleString()}</td>
                    <td>{streakOf(user)}</td>
                    <td>{formatDate(user.date_joined ?? user.joined_at)}</td>
                    <td>
                      <span className={`status-pill ${user.is_active ? "status-pill--ok" : "status-pill--off"}`}>
                        {user.is_active ? "Active" : "Inactive"}
                      </span>
                    </td>
                    <td>
                      <div className="admin-cell__actions">
                        <Dropdown trigger={<IconButton label={`Actions for ${user.display_name || user.email}`}><MoreVertical size={16} /></IconButton>}>
                          {ALL_ROLES.filter((item) => item !== user.role).map((item) => (
                            <DropdownItem key={item} icon={ShieldCheck} onClick={() => openRole(user, item)}>
                              Make {item}
                            </DropdownItem>
                          ))}
                          <div className="dropdown__divider" />
                          {user.is_active ? (
                            <DropdownItem danger icon={UserX} onClick={() => openActive(user, false)}>
                              Deactivate
                            </DropdownItem>
                          ) : (
                            <DropdownItem icon={UserCheck} onClick={() => openActive(user, true)}>
                              Reactivate
                            </DropdownItem>
                          )}
                        </Dropdown>
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

      <ConfirmDialog
        open={Boolean(pending)}
        onClose={() => setPending(null)}
        onConfirm={confirm}
        busy={busy}
        variant={pending?.type === "active" && pending.value === false ? "danger" : "primary"}
        confirmLabel="Confirm change"
        title={pending?.type === "active" ? (pending.value ? "Reactivate member" : "Deactivate member") : "Change role"}
        message={
          pending
            ? pending.type === "role"
              ? `Set ${pending.user.display_name || pending.user.email} to the ${pending.value} role? This changes what they can access.`
              : pending.value
                ? `Reactivate ${pending.user.display_name || pending.user.email}? They will be able to sign in again.`
                : `Deactivate ${pending.user.display_name || pending.user.email}? They will be signed out and blocked from logging in.`
            : ""
        }
      />
    </div>
  );
}
