import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  Award,
  Bell,
  CalendarClock,
  CheckCheck,
  Check,
  Megaphone,
  MessageSquare,
  MessagesSquare,
  Sparkles,
  Trophy,
  X,
} from "lucide-react";
import { api, endpoints } from "../../services/api";
import { useAsync } from "../../hooks";
import { useNotificationCount } from "../../hooks/useNotifications";
import { useToast } from "../../context/ToastContext";
import {
  Button,
  EmptyState,
  ErrorState,
  IconButton,
  Pagination,
  Skeleton,
  Tabs,
} from "../../components/ui";
import { asList, formatDate, formatRelative, resolveRef } from "./helpers";
import "./app.css";

const KIND_ICONS = {
  comment: MessageSquare,
  reply: MessagesSquare,
  mentorship_update: Sparkles,
  session_reminder: CalendarClock,
  course_announcement: Megaphone,
  challenge_result: Trophy,
  achievement: Award,
};

function iconForKind(kind) {
  return KIND_ICONS[kind] ?? Bell;
}

// Deep links are best-effort: the notification carries the object reference in
// different fields per kind, so we resolve what we can and fall back to the
// section landing page rather than dropping the user on a dead route.
function linkFor(notification) {
  const explicit = notification.url ?? notification.link ?? notification.target_url;
  if (typeof explicit === "string" && explicit.startsWith("/")) return explicit;

  const objType = String(notification.object_type ?? "").toLowerCase();
  const id = notification.object_id;

  switch (notification.kind) {
    case "comment":
    case "reply": {
      const postId = notification.post ?? (objType.includes("post") ? id : null);
      return postId ? `/community/posts/${postId}` : "/community";
    }
    case "course_announcement": {
      const course = resolveRef(notification.course);
      return course.id ? `/learning/${typeof notification.course === "object" ? (notification.course.slug ?? course.id) : course.id}` : "/learning";
    }
    case "challenge_result": {
      const challenge = notification.challenge ?? (objType.includes("challenge") ? id : null);
      return challenge ? `/challenges/${typeof challenge === "object" ? challenge.id : challenge}` : "/challenges";
    }
    case "mentorship_update":
    case "session_reminder":
      return "/mentorships";
    case "achievement":
      return "/achievements";
    default:
      if (objType.includes("post") && id) return `/community/posts/${id}`;
      if (objType.includes("project") && id) return `/community/projects/${id}`;
      return null;
  }
}

function NotificationRow({ notification, onMarkRead, onDismiss, busy }) {
  const Icon = iconForKind(notification.kind);
  const unread = !notification.is_read;
  const link = linkFor(notification);
  const title = notification.title || notification.message || "Notification";
  const body = notification.title && notification.message ? notification.message : null;

  const inner = (
    <div className={`notif-item ${unread ? "notif-item--unread" : ""}`}>
      <span className="mini-item__icon" style={unread ? undefined : { background: "transparent", color: "var(--text-muted)" }}>
        <Icon size={16} aria-hidden="true" />
      </span>
      <div className="notif-item__body">
        <div className="notif-item__title">{title}</div>
        {body ? <p className="notif-item__text">{body}</p> : null}
        <div className="notif-item__time" title={formatDate(notification.created_at)}>
          {unread ? "Unread · " : ""}
          {notification.created_at ? formatRelative(notification.created_at) : ""}
        </div>
      </div>
      <div className="notif-item__actions">
        {unread ? (
          <IconButton
            label="Mark as read"
            variant="ghost"
            disabled={busy}
            onClick={(event) => {
              event.preventDefault();
              event.stopPropagation();
              onMarkRead(notification);
            }}
          >
            <Check size={16} />
          </IconButton>
        ) : null}
        <IconButton
          label="Dismiss notification"
          variant="ghost"
          disabled={busy}
          onClick={(event) => {
            event.preventDefault();
            event.stopPropagation();
            onDismiss(notification);
          }}
        >
          <X size={16} />
        </IconButton>
      </div>
    </div>
  );

  if (link) {
    return (
      <li>
        <Link to={link} style={{ color: "inherit" }}>
          {inner}
        </Link>
      </li>
    );
  }
  return <li>{inner}</li>;
}

export default function Notifications() {
  const toast = useToast();
  const { refresh: refreshCount } = useNotificationCount();
  const [tab, setTab] = useState("all");
  const [page, setPage] = useState(1);
  const unreadOnly = tab === "unread";

  const { data, setData, loading, error, reload } = useAsync(
    (signal) => api.get(endpoints.notifications, { signal, params: { unread_only: unreadOnly ? "true" : undefined, page } }),
    [tab, page]
  );

  const items = useMemo(() => asList(data), [data]);
  const count = data?.count ?? items.length;
  const pageSize = data?.page_size ?? 20;

  const [busyId, setBusyId] = useState(null);
  const [busyAll, setBusyAll] = useState(false);

  const markRead = async (notification) => {
    setBusyId(notification.id);
    try {
      await api.post(`/notifications/${notification.id}/read/`);
      setData((current) => ({
        ...current,
        results: (current?.results ?? []).map((item) => (item.id === notification.id ? { ...item, is_read: true } : item)),
      }));
      refreshCount();
    } catch (err) {
      toast.error(err?.detail || "Could not mark that as read.");
    } finally {
      setBusyId(null);
    }
  };

  const markAllRead = async () => {
    setBusyAll(true);
    try {
      await api.post("/notifications/read-all/");
      toast.success("All notifications marked as read.");
      reload();
      refreshCount();
    } catch (err) {
      toast.error(err?.detail || "Could not mark all as read.");
    } finally {
      setBusyAll(false);
    }
  };

  const dismiss = async (notification) => {
    setBusyId(notification.id);
    try {
      await api.del(`/notifications/${notification.id}/`);
      setData((current) => ({
        ...current,
        results: (current?.results ?? []).filter((item) => item.id !== notification.id),
        count: Math.max(0, (current?.count ?? 1) - 1),
      }));
      refreshCount();
    } catch (err) {
      toast.error(err?.detail || "Could not dismiss that notification.");
    } finally {
      setBusyId(null);
    }
  };

  const unreadCount = items.filter((item) => !item.is_read).length;

  return (
    <div className="app-page">
      <header className="app-page__head row" style={{ justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <h1 className="app-page__title">Notifications</h1>
          <p className="app-page__sub">Replies, mentorship updates, announcements and achievements.</p>
        </div>
        <Button variant="ghost" onClick={markAllRead} loading={busyAll} disabled={loading || unreadCount === 0}>
          <CheckCheck size={16} aria-hidden="true" /> Mark all read
        </Button>
      </header>

      <Tabs
        items={[
          { value: "all", label: "All" },
          { value: "unread", label: "Unread" },
        ]}
        value={tab}
        onChange={(value) => {
          setTab(value);
          setPage(1);
        }}
        ariaLabel="Notification filters"
      />

      <div aria-live="polite">
        {loading ? (
          <div className="notif-list">
            {[0, 1, 2, 3].map((key) => (
              <Skeleton key={key} style={{ height: 76 }} />
            ))}
          </div>
        ) : null}

        {!loading && error ? (
          <ErrorState error={error} onRetry={reload} title="We couldn't load notifications" />
        ) : null}

        {!loading && !error && items.length === 0 ? (
          <EmptyState
            icon={Bell}
            title={unreadOnly ? "No unread notifications" : "Nothing here yet"}
            description={
              unreadOnly
                ? "You're all caught up. New activity will show up here."
                : "When someone replies to you, a mentor responds, or a badge unlocks, it lands here."
            }
            action={unreadOnly ? <Button variant="ghost" onClick={() => setTab("all")}>View all</Button> : null}
          />
        ) : null}

        {!loading && !error && items.length > 0 ? (
          <>
            <ul className="notif-list" style={{ listStyle: "none", padding: 0 }}>
              {items.map((notification, index) => (
                <NotificationRow
                  key={notification.id ?? index}
                  notification={notification}
                  onMarkRead={markRead}
                  onDismiss={dismiss}
                  busy={busyId === notification.id}
                />
              ))}
            </ul>
            <Pagination count={count} page={page} pageSize={pageSize} onPageChange={setPage} />
          </>
        ) : null}
      </div>
    </div>
  );
}
