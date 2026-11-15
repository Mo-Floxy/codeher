import { useCallback, useMemo, useState } from "react";
import { CalendarClock, CalendarPlus, Clock, Video } from "lucide-react";
import { api, endpoints } from "../../services/api";
import { useAsync } from "../../hooks";
import { useAuth } from "../../context/AuthContext";
import { useToast } from "../../context/ToastContext";
import {
  Alert,
  Badge,
  Button,
  Chip,
  ConfirmDialog,
  EmptyState,
  ErrorState,
  Field,
  Input,
  Modal,
  Select,
  SkeletonList,
  Tabs,
  Textarea,
  UserCell,
} from "../../components/ui";
import {
  errorText,
  excerpt,
  formatDateTime,
  formatDuration,
  isPastIso,
  itemsFrom,
  learnerOf,
  mentorIdOf,
  mentorOf,
  slotLabel,
  statusOf,
  statusVariant,
} from "./mentorshipUtils";
import "./mentorship.css";

function StatusBadge({ status }) {
  return <Badge variant={statusVariant(status)}>{status}</Badge>;
}

function patchListData(setData, id, patch) {
  setData((current) => {
    if (!current) return current;
    const results = itemsFrom(current).map((item) => (String(item.id) === String(id) ? patch(item) : item));
    return Array.isArray(current) ? results : { ...current, results };
  });
}

function RequestActionModal({ action, request, onClose, onDone }) {
  const toast = useToast();
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState(null);
  const accept = action === "accept";

  const submit = async () => {
    if (!accept && !note.trim()) {
      setFailure({ detail: "Add a short reason so the learner knows what to improve." });
      return;
    }
    setBusy(true);
    setFailure(null);
    try {
      await api.post(
        `/mentorship/requests/${request.id}/${accept ? "accept" : "decline"}/`,
        accept ? { note: note.trim() } : { reason: note.trim() }
      );
      toast.success(accept ? "Request accepted — now schedule a session." : "Request declined politely.");
      onDone(request, accept ? "accepted" : "declined");
    } catch (err) {
      setFailure(err);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal
      open={Boolean(request && action)}
      onClose={onClose}
      title={accept ? "Accept mentorship request" : "Decline mentorship request"}
      description={
        accept
          ? "Your note is sent to the learner and can point at a first step or session time."
          : "A kind reason helps the learner grow — they will see it."
      }
      footer={
        <>
          <Button variant="ghost" onClick={onClose} disabled={busy}>
            Cancel
          </Button>
          <Button variant={accept ? "primary" : "danger"} onClick={submit} loading={busy}>
            {accept ? "Accept request" : "Decline request"}
          </Button>
        </>
      }
    >
      <Field
        label={accept ? "Note for the learner (optional)" : "Reason (required)"}
        required={!accept}
        htmlFor="request-action-note"
      >
        <Textarea
          id="request-action-note"
          data-autofocus
          rows={4}
          value={note}
          onChange={(event) => setNote(event.target.value)}
          placeholder={accept ? "Looking forward to it — bring a list of your goals…" : "I am currently at capacity, but…"}
        />
      </Field>
      {failure && <Alert variant="error">{errorText(failure)}</Alert>}
    </Modal>
  );
}

function ScheduleSessionModal({ open, onClose, requests, onCreated }) {
  const toast = useToast();
  const [form, setForm] = useState({ request: "", starts_at: "", duration_minutes: "30", meeting_url: "", agenda: "" });
  const [errors, setErrors] = useState({});
  const [failure, setFailure] = useState(null);
  const [busy, setBusy] = useState(false);

  const accepted = useMemo(() => requests.filter((item) => statusOf(item) === "accepted"), [requests]);
  const options = accepted.map((item) => {
    const learner = learnerOf(item);
    const label = `${learner?.display_name || learner?.username || "Learner"} — ${item.goal ? excerpt(item.goal, 40) : `request #${item.id}`}`;
    return { value: item.id, label };
  });

  const submit = async () => {
    const clientErrors = {};
    if (!form.request) clientErrors.request = "Pick one of your accepted requests.";
    const starts = form.starts_at ? new Date(form.starts_at) : null;
    if (!starts || Number.isNaN(starts.getTime())) clientErrors.starts_at = "Choose a date and time.";
    const duration = Number(form.duration_minutes);
    if (!Number.isFinite(duration) || duration < 5 || duration > 240) clientErrors.duration_minutes = "Between 5 and 240 minutes.";
    if (Object.keys(clientErrors).length) {
      setErrors(clientErrors);
      return;
    }
    setBusy(true);
    setFailure(null);
    try {
      await api.post("/mentorship/sessions/", {
        request: Number(form.request),
        starts_at: starts.toISOString(),
        duration_minutes: duration,
        meeting_url: form.meeting_url.trim() || undefined,
        agenda: form.agenda.trim() || undefined,
      });
      toast.success("Session scheduled — the learner sees the invitation.");
      setForm({ request: "", starts_at: "", duration_minutes: "30", meeting_url: "", agenda: "" });
      onCreated();
      onClose();
    } catch (err) {
      setErrors(Object.fromEntries(["request", "starts_at", "duration_minutes", "meeting_url", "agenda"].filter((key) => err?.fieldErrors?.[key]?.[0]).map((key) => [key, err.fieldErrors[key][0]])));
      setFailure(err);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Schedule a session"
      description="Sessions attach to an accepted mentorship request. The meeting link stays private to you two."
      footer={
        <>
          <Button variant="ghost" onClick={onClose} disabled={busy}>
            Cancel
          </Button>
          <Button onClick={submit} loading={busy}>
            <CalendarPlus size={15} aria-hidden="true" /> Schedule
          </Button>
        </>
      }
    >
      {accepted.length === 0 ? (
        <Alert variant="info">
          You can schedule sessions once a learner request is accepted. Manage requests in the
          “Incoming requests” tab.
        </Alert>
      ) : (
        <div className="form-grid">
          <Field label="Accepted request" required htmlFor="session-request" error={errors.request}>
            <Select
              id="session-request"
              data-autofocus
              value={form.request}
              onChange={(event) => setForm((f) => ({ ...f, request: event.target.value }))}
              options={[{ value: "", label: "Choose a request…" }, ...options]}
            />
          </Field>
          <div className="form-grid form-grid--2">
            <Field label="Starts at" required htmlFor="session-starts" error={errors.starts_at}>
              <Input
                id="session-starts"
                type="datetime-local"
                value={form.starts_at}
                onChange={(event) => setForm((f) => ({ ...f, starts_at: event.target.value }))}
                error={errors.starts_at}
              />
            </Field>
            <Field label="Duration (minutes)" required htmlFor="session-duration" error={errors.duration_minutes}>
              <Input
                id="session-duration"
                type="number"
                min={5}
                max={240}
                step={5}
                value={form.duration_minutes}
                onChange={(event) => setForm((f) => ({ ...f, duration_minutes: event.target.value }))}
                error={errors.duration_minutes}
              />
            </Field>
          </div>
          <Field label="Meeting URL (optional)" htmlFor="session-meeting" hint="Only the two participants ever see this link." error={errors.meeting_url}>
            <Input
              id="session-meeting"
              type="url"
              value={form.meeting_url}
              onChange={(event) => setForm((f) => ({ ...f, meeting_url: event.target.value }))}
              placeholder="https://meet.example.com/room"
              error={errors.meeting_url}
            />
          </Field>
          <Field label="Agenda (optional)" htmlFor="session-agenda" error={errors.agenda}>
            <Textarea
              id="session-agenda"
              rows={3}
              value={form.agenda}
              onChange={(event) => setForm((f) => ({ ...f, agenda: event.target.value }))}
              placeholder="What we will cover, what to prepare."
            />
          </Field>
          {failure && !failure?.fieldErrors?.starts_at && <Alert variant="error">{errorText(failure)}</Alert>}
        </div>
      )}
    </Modal>
  );
}

export default function MyMentorships() {
  const { isMentor, isAdmin } = useAuth();
  const toast = useToast();
  const canIncoming = isMentor || isAdmin;
  const isLearnerOnly = !canIncoming;

  const [tab, setTab] = useState("requests");
  const [cancelTarget, setCancelTarget] = useState(null);
  const [cancelling, setCancelling] = useState(false);
  const [actionModal, setActionModal] = useState(null);
  const [scheduleOpen, setScheduleOpen] = useState(false);
  const [attendanceBusy, setAttendanceBusy] = useState(null);

  const outgoing = useAsync(
    (signal) => api.get(endpoints.mentorRequests, { signal, params: { page_size: 50 } }),
    []
  );
  const incoming = useAsync(
    (signal) => api.get("/mentorship/requests/incoming/", { signal }),
    [],
    { skip: !canIncoming || (tab !== "incoming" && tab !== "sessions") }
  );
  const sessions = useAsync(
    (signal) => api.get("/mentorship/sessions/", { signal, params: { page_size: 50 } }),
    [],
    { skip: tab !== "sessions" }
  );

  const cancelRequest = async () => {
    if (!cancelTarget) return;
    setCancelling(true);
    try {
      await api.post(`/mentorship/requests/${cancelTarget.id}/cancel/`, {});
      patchListData(outgoing.setData, cancelTarget.id, (item) => ({ ...item, status: "cancelled" }));
      toast.success("Request cancelled.");
      setCancelTarget(null);
    } catch (err) {
      toast.error(errorText(err));
    } finally {
      setCancelling(false);
    }
  };

  const handleActionDone = useCallback(
    (request, status) => {
      patchListData(incoming.setData, request.id, (item) => ({ ...item, status }));
      setActionModal(null);
    },
    [incoming]
  );

  const sendAttendance = async (session, attended) => {
    setAttendanceBusy(session.id);
    try {
      await api.post(`/mentorship/sessions/${session.id}/attendance/`, { attended });
      patchListData(sessions.setData, session.id, (item) => ({ ...item, attended }));
      toast.success(attended ? "Attendance recorded — thanks!" : "Attendance removed.");
    } catch (err) {
      toast.error(errorText(err));
    } finally {
      setAttendanceBusy(null);
    }
  };

  const tabItems = [
    { value: "requests", label: "My requests" },
    ...(canIncoming ? [{ value: "incoming", label: "Incoming requests" }] : []),
    { value: "sessions", label: "Sessions" },
  ];

  const renderRequests = (state, { incomingView }) => {
    const rows = itemsFrom(state.data);
    if (state.error && !rows.length) return <ErrorState error={state.error} onRetry={state.reload} />;
    if (state.loading && !rows.length) return <SkeletonList count={3} height={170} />;
    if (!rows.length) {
      return (
        <EmptyState
          icon={incomingView ? Clock : CalendarClock}
          title={incomingView ? "Your inbox is empty" : "No mentorship requests yet"}
          description={
            incomingView
              ? "When learners ask you for mentorship, their requests land here."
              : "Find a mentor in the directory and send your first request — your goal, message and slots travel with it."
          }
          action={
            incomingView ? null : (
              <Button variant="ghost" to="/mentorship">
                Browse mentors
              </Button>
            )
          }
        />
      );
    }
    return (
      <div className="workspace-body">
        {rows.map((request) => {
          const status = statusOf(request);
          const person = incomingView ? learnerOf(request) : mentorOf(request);
          const linkTo = incomingView
            ? person?.id != null
              ? `/members/${person.id}`
              : undefined
            : mentorIdOf(request) != null
              ? `/mentorship/${mentorIdOf(request)}`
              : undefined;
          const slots = Array.isArray(request.preferred_slots) ? request.preferred_slots : [];
          return (
            <article className="card request-card" key={request.id}>
              <header className="request-card__head">
                <UserCell user={person ?? { display_name: incomingView ? "Learner" : "Mentor" }} to={linkTo} />
                <StatusBadge status={status} />
              </header>
              {request.goal && <p className="request-card__goal">{request.goal}</p>}
              {request.message && <p className="muted" style={{ fontSize: "var(--fs-sm)" }}>{excerpt(request.message, 180)}</p>}
              {slots.length > 0 && (
                <div className="slot-list-inline">
                  {slots.map((slot, index) => (
                    <Chip key={index}>{slotLabel(slot)}</Chip>
                  ))}
                </div>
              )}
              <footer className="request-card__foot">
                <span className="muted" style={{ fontSize: "var(--fs-xs)" }}>
                  {request.created_at ? `Sent ${formatDateTime(request.created_at)}` : ""}
                </span>
                <span style={{ marginLeft: "auto" }} className="row">
                  {!incomingView && status === "pending" && (
                    <Button variant="danger" size="sm" onClick={() => setCancelTarget(request)}>
                      Cancel request
                    </Button>
                  )}
                  {incomingView && status === "pending" && (
                    <>
                      <Button variant="ghost" size="sm" onClick={() => setActionModal({ action: "decline", request })}>
                        Decline
                      </Button>
                      <Button size="sm" onClick={() => setActionModal({ action: "accept", request })}>
                        Accept
                      </Button>
                    </>
                  )}
                </span>
              </footer>
            </article>
          );
        })}
      </div>
    );
  };

  const renderSessions = () => {
    const rows = itemsFrom(sessions.data);
    if (sessions.error && !rows.length) return <ErrorState error={sessions.error} onRetry={sessions.reload} />;
    if (sessions.loading && !rows.length) return <SkeletonList count={3} height={170} />;
    if (!rows.length) {
      return (
        <EmptyState
          icon={CalendarClock}
          title="No sessions scheduled yet"
          description={
            canIncoming
              ? "Sessions appear once a mentorship request is accepted."
              : "Your mentor schedules sessions once they accept your request."
          }
        />
      );
    }
    return (
      <div className="workspace-body">
        {rows.map((session) => {
          const past = isPastIso(session.starts_at);
          const status = statusOf(session, past ? "completed" : "scheduled");
          const attended = Boolean(session.attended ?? session.attendance?.attended ?? session.marked_attended);
          const agenda = session.agenda || "";
          const learner = learnerOf(session.request && typeof session.request === "object" ? session.request : {});
          return (
            <article className="card session-card" key={session.id}>
              <header className="session-card__head">
                <h2 style={{ fontSize: "var(--fs-base)" }}>{agenda ? excerpt(agenda, 70) : `Session #${session.id}`}</h2>
                <StatusBadge status={status} />
              </header>
              <div className="session-meta">
                <span>
                  <CalendarClock size={14} aria-hidden="true" /> {formatDateTime(session.starts_at) || "Time to be confirmed"}
                </span>
                {session.duration_minutes ? (
                  <span>
                    <Clock size={14} aria-hidden="true" /> {formatDuration(session.duration_minutes)}
                  </span>
                ) : null}
                {learner?.display_name ? <span>with {learner.display_name}</span> : null}
              </div>
              {agenda && <p className="muted" style={{ fontSize: "var(--fs-sm)" }}>{agenda}</p>}
              <footer className="session-card__foot">
                {session.meeting_url ? (
                  <Button variant="outline" size="sm" href={session.meeting_url} aria-label="Join meeting (opens in a new tab)">
                    <Video size={14} aria-hidden="true" /> Join meeting
                  </Button>
                ) : (
                  <span className="muted" style={{ fontSize: "var(--fs-xs)" }}>
                    Meeting link visible to participants only.
                  </span>
                )}
                <span style={{ marginLeft: "auto" }} className="row">
                  {isLearnerOnly && past && (
                    attended ? (
                      <>
                        <Badge variant="success">Attendance recorded</Badge>
                        <Button variant="link" size="sm" disabled={attendanceBusy === session.id} onClick={() => sendAttendance(session, false)}>
                          Undo
                        </Button>
                      </>
                    ) : (
                      <Button variant="ghost" size="sm" loading={attendanceBusy === session.id} onClick={() => sendAttendance(session, true)}>
                        Mark attended
                      </Button>
                    )
                  )}
                </span>
              </footer>
            </article>
          );
        })}
      </div>
    );
  };

  let panel;
  let panelLabel;
  let panelLoading = false;
  if (tab === "requests") {
    panelLabel = "My mentorship requests";
    panelLoading = outgoing.loading;
    panel = renderRequests(outgoing, { incomingView: false });
  } else if (tab === "incoming") {
    panelLabel = "Incoming mentorship requests";
    panelLoading = incoming.loading;
    panel = canIncoming ? renderRequests(incoming, { incomingView: true }) : null;
  } else {
    panelLabel = "Mentorship sessions";
    panelLoading = sessions.loading;
    panel = renderSessions();
  }

  return (
    <div className="stack" style={{ gap: "var(--sp-2)" }}>
      <header className="mentorship-header__row" style={{ paddingTop: 0 }}>
        <div className="stack" style={{ gap: "var(--sp-2)" }}>
          <span className="eyebrow">Mentorship workspace</span>
          <h1>My mentorships</h1>
          <p className="muted" style={{ fontSize: "var(--fs-sm)" }}>
            Requests, matches and sessions in one place — actions depend on your role.
          </p>
        </div>
        {canIncoming && tab === "sessions" && (
          <Button onClick={() => setScheduleOpen(true)}>
            <CalendarPlus size={16} aria-hidden="true" /> Schedule session
          </Button>
        )}
      </header>

      <Tabs items={tabItems} value={tab} onChange={setTab} ariaLabel="Mentorship workspace" />

      <section aria-label={panelLabel} aria-live="polite" aria-busy={panelLoading} className="stack" style={{ gap: "var(--sp-3)" }}>
        {panel}
      </section>

      <ConfirmDialog
        open={Boolean(cancelTarget)}
        onClose={() => setCancelTarget(null)}
        onConfirm={cancelRequest}
        busy={cancelling}
        title="Cancel this request?"
        message="The mentor will no longer see it in their inbox. You can always send a new one."
        confirmLabel="Cancel request"
      />

      {canIncoming && (
        <>
          <RequestActionModal
            action={actionModal?.action}
            request={actionModal?.request}
            onClose={() => setActionModal(null)}
            onDone={handleActionDone}
          />
          <ScheduleSessionModal
            open={scheduleOpen}
            onClose={() => setScheduleOpen(false)}
            requests={itemsFrom(incoming.data)}
            onCreated={sessions.reload}
          />
        </>
      )}
    </div>
  );
}
