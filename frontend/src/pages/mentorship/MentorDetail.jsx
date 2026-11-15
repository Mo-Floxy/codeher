import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { ArrowLeft, CheckCircle2, Clock, Plus, Send, X } from "lucide-react";
import { api, endpoints } from "../../services/api";
import { useAsync } from "../../hooks";
import { useAuth } from "../../context/AuthContext";
import { useToast } from "../../context/ToastContext";
import {
  Alert,
  Avatar,
  Badge,
  Button,
  Chip,
  ChipRow,
  EmptyState,
  ErrorState,
  Field,
  IconButton,
  Input,
  Loading,
  Select,
  Skeleton,
  SkeletonText,
  Textarea,
} from "../../components/ui";
import {
  WEEKDAYS,
  errorText,
  itemsFrom,
  mentorAvatarUser,
  mentorIdOf,
  mentorName,
  slotLabel,
  statusOf,
} from "./mentorshipUtils";
import "./mentorship.css";

function RequestForm({ mentorId, onSent }) {
  const [goal, setGoal] = useState("");
  const [message, setMessage] = useState("");
  const [slots, setSlots] = useState([{ weekday: "monday", time: "" }]);
  const [errors, setErrors] = useState({});
  const [failure, setFailure] = useState(null);
  const [busy, setBusy] = useState(false);

  const updateSlot = (index, key, value) => {
    setSlots((current) => current.map((slot, i) => (i === index ? { ...slot, [key]: value } : slot)));
  };

  const submit = async (event) => {
    event.preventDefault();
    const clientErrors = {};
    if (!goal.trim()) clientErrors.goal = "Tell your mentor what you want to achieve.";
    if (!message.trim()) clientErrors.message = "Introduce yourself and why this mentor fits.";
    if (!slots.length || slots.some((slot) => !slot.time)) {
      clientErrors.slots = "Give a time for every preferred slot.";
    }
    if (Object.keys(clientErrors).length) {
      setErrors(clientErrors);
      return;
    }

    setBusy(true);
    setFailure(null);
    try {
      await api.post(endpoints.mentorRequests, {
        mentor: Number.isNaN(Number(mentorId)) ? mentorId : Number(mentorId),
        goal: goal.trim(),
        message: message.trim(),
        preferred_slots: slots.map(({ weekday, time }) => ({ weekday, time })),
      });
      onSent();
    } catch (err) {
      const fieldErrors = err?.fieldErrors ?? {};
      const mapped = {};
      for (const key of ["mentor", "goal", "message", "preferred_slots"]) {
        if (fieldErrors[key]?.[0]) mapped[key] = fieldErrors[key][0];
      }
      setErrors(mapped);
      // A 400 duplicate guard usually arrives as { detail } — surface it inline instead of silently failing.
      setFailure(err);
    } finally {
      setBusy(false);
    }
  };

  return (
    <form className="request-form" onSubmit={submit} noValidate aria-label="Mentorship request">
      <Field label="Your goal" required htmlFor="request-goal" error={errors.goal}>
        <Input
          id="request-goal"
          data-autofocus
          maxLength={200}
          value={goal}
          onChange={(event) => setGoal(event.target.value)}
          placeholder="e.g. Finish the React path and ship my first portfolio site"
          error={errors.goal}
        />
      </Field>

      <Field label="Message" required htmlFor="request-message" error={errors.message} hint="Why this mentor, where you are, what you hope for.">
        <Textarea
          id="request-message"
          rows={5}
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          placeholder="Hi! I am working through the frontend path and…"
          error={errors.message}
        />
      </Field>

      <div className="field">
        <span className="field__label" id="slots-label">
          Preferred slots
        </span>
        <p className="field__hint">Pick weekday and time combinations that work for you.</p>
        <div className="slot-list" role="group" aria-labelledby="slots-label">
          {slots.map((slot, index) => (
            <div className="slot-row" key={index}>
              <Select
                aria-label={`Weekday for slot ${index + 1}`}
                value={slot.weekday}
                onChange={(event) => updateSlot(index, "weekday", event.target.value)}
                options={WEEKDAYS}
              />
              <Input
                type="time"
                aria-label={`Time for slot ${index + 1}`}
                value={slot.time}
                onChange={(event) => updateSlot(index, "time", event.target.value)}
              />
              <IconButton
                label={`Remove slot ${index + 1}`}
                onClick={() => setSlots((current) => current.filter((_, i) => i !== index))}
                disabled={slots.length <= 1}
              >
                <X size={16} aria-hidden="true" />
              </IconButton>
            </div>
          ))}
        </div>
        <div className="row">
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => setSlots((current) => [...current, { weekday: "monday", time: "" }])}
          >
            <Plus size={14} aria-hidden="true" /> Add another slot
          </Button>
        </div>
        {(errors.slots || errors.preferred_slots) && (
          <p className="field__error" role="alert">
            {errors.slots || errors.preferred_slots}
          </p>
        )}
      </div>

      {failure && <Alert variant="error">{errorText(failure)}</Alert>}

      <Button type="submit" loading={busy}>
        <Send size={15} aria-hidden="true" /> Send mentorship request
      </Button>
    </form>
  );
}

export default function MentorDetail() {
  const { id } = useParams();
  const { isAuthenticated } = useAuth();
  const toast = useToast();

  const mentorState = useAsync((signal) => api.get(`/mentorship/mentors/${id}/`, { signal }), [id]);
  const requestsState = useAsync(
    (signal) => api.get(endpoints.mentorRequests, { signal, params: { page_size: 50 } }),
    [],
    { skip: !isAuthenticated }
  );

  const mentor = mentorState.data;

  const existing = useMemo(() => {
    if (!requestsState.data) return null;
    return itemsFrom(requestsState.data).find((request) => String(mentorIdOf(request)) === String(id)) ?? null;
  }, [requestsState.data, id]);

  const existingStatus = existing ? statusOf(existing) : null;

  if (mentorState.error) {
    return (
      <section className="container section">
        <ErrorState error={mentorState.error} onRetry={mentorState.reload} title="We could not load this mentor" />
      </section>
    );
  }

  if (mentorState.loading && !mentor) {
    return (
      <section className="container section" aria-busy="true" aria-live="polite">
        <div className="card stack">
          <Skeleton style={{ height: 90, width: 90, borderRadius: "50%" }} />
          <Skeleton className="skeleton--title" />
          <SkeletonText lines={4} />
        </div>
      </section>
    );
  }

  if (!mentor) {
    return (
      <section className="container section">
        <EmptyState
          icon={X}
          title="Mentor not found"
          description="This profile is no longer listed — mentors must stay approved to appear here."
          action={
            <Button variant="ghost" to="/mentorship">
              Back to the directory
            </Button>
          }
        />
      </section>
    );
  }

  const expertise = (mentor.expertise ?? []).map((value) => (typeof value === "string" ? value : value?.name)).filter(Boolean);
  const availabilitySlots = Array.isArray(mentor.availability) ? mentor.availability : [];
  const headline = mentor.headline ?? mentor.user?.headline ?? "";
  const bio = mentor.bio ?? mentor.user?.bio ?? "";
  const note = mentor.availability_note ?? "";

  return (
    <section className="container" style={{ paddingBlock: "var(--sp-6) var(--sp-9)" }}>
      <nav aria-label="Breadcrumb" style={{ marginBottom: "var(--sp-4)" }}>
        <Button variant="link" size="sm" to="/mentorship">
          <ArrowLeft size={15} aria-hidden="true" /> All mentors
        </Button>
      </nav>

      <div className="mentor-detail-layout">
        <article className="card stack">
          <header className="mentor-hero">
            <Avatar user={mentorAvatarUser(mentor)} size="xl" />
            <div className="mentor-hero__identity">
              <h1>{mentorName(mentor)}</h1>
              {headline && <p className="lead">{headline}</p>}
              {note && (
                <p className="mentor-card__availability">
                  <Clock size={14} aria-hidden="true" /> {note}
                </p>
              )}
              {mentor.hourly_openness ? <span className="muted" style={{ fontSize: "var(--fs-xs)" }}>Weekly commitment: {mentor.hourly_openness}</span> : null}
            </div>
          </header>

          {expertise.length > 0 && (
            <>
              <h2 style={{ fontSize: "var(--fs-base)" }}>Expertise</h2>
              <ChipRow>
                {expertise.map((value) => (
                  <Chip key={value}>{value}</Chip>
                ))}
              </ChipRow>
            </>
          )}

          {availabilitySlots.length > 0 && (
            <>
              <h2 style={{ fontSize: "var(--fs-base)" }}>Usual availability</h2>
              <ChipRow>
                {availabilitySlots.map((slot, index) => (
                  <Chip key={index}>{slotLabel(slot)}</Chip>
                ))}
              </ChipRow>
            </>
          )}

          <h2 style={{ fontSize: "var(--fs-base)" }}>About</h2>
          <p className="mentor-bio">{bio || "This mentor has not written a bio yet."}</p>
        </article>

        <aside className="card stack status-panel" aria-label="Mentorship request" aria-live="polite">
          <h2 style={{ fontSize: "var(--fs-base)" }}>Request mentorship</h2>

          {!isAuthenticated ? (
            <>
              <Alert variant="info">
                You need an account so the mentor can see who is asking and reply to you.
              </Alert>
              <Button to="/signin">
                Sign in to send a request <Send size={15} aria-hidden="true" />
              </Button>
            </>
          ) : requestsState.loading && !requestsState.data ? (
            <Loading label="Checking your requests" />
          ) : requestsState.error ? (
            <ErrorState error={requestsState.error} onRetry={requestsState.reload} title="Could not check your requests" />
          ) : existingStatus === "pending" ? (
            <>
              <p>
                <Badge variant="warning">Pending</Badge>
              </p>
              <p className="muted" style={{ fontSize: "var(--fs-sm)" }}>
                You already have a pending request with this mentor, so no duplicate was sent. Follow
                its progress in your mentorship workspace.
              </p>
              <Button variant="outline" to="/mentorships">
                Track my requests
              </Button>
            </>
          ) : existingStatus === "accepted" ? (
            <>
              <p>
                <Badge variant="success">
                  <CheckCircle2 size={12} aria-hidden="true" /> Accepted
                </Badge>
              </p>
              <p className="muted" style={{ fontSize: "var(--fs-sm)" }}>
                You are matched with this mentor. Sessions are managed in your workspace.
              </p>
              <Button variant="outline" to="/mentorships">
                Open sessions
              </Button>
            </>
          ) : (
            <>
              {existing && (
                <Alert variant="info">
                  Your earlier request on this mentor is “{existingStatus}” — you may send a new one.
                </Alert>
              )}
              <RequestForm
                mentorId={id}
                onSent={() => {
                  toast.success("Mentorship request sent — the mentor will review it soon.");
                  requestsState.reload();
                }}
              />
            </>
          )}
        </aside>
      </div>
    </section>
  );
}
