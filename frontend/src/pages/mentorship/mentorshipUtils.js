export function itemsFrom(payload) {
  if (Array.isArray(payload)) return payload;
  return payload?.results ?? [];
}

export function excerpt(text, max = 160) {
  const clean = String(text ?? "").replace(/\s+/g, " ").trim();
  if (!clean) return "";
  if (clean.length <= max) return clean;
  return `${clean.slice(0, max - 1).trimEnd()}…`;
}

export function errorText(err) {
  if (!err) return "Unexpected error.";
  return err.detail || err.messageFor?.("__default__") || err.message || "Unexpected error.";
}

export const WEEKDAYS = [
  { value: "monday", label: "Monday" },
  { value: "tuesday", label: "Tuesday" },
  { value: "wednesday", label: "Wednesday" },
  { value: "thursday", label: "Thursday" },
  { value: "friday", label: "Friday" },
  { value: "saturday", label: "Saturday" },
  { value: "sunday", label: "Sunday" },
];

const STATUS_VARIANTS = {
  pending: "warning",
  accepted: "success",
  declined: "danger",
  cancelled: "neutral",
  completed: "brand",
  scheduled: "info",
};

export function statusVariant(status) {
  return STATUS_VARIANTS[String(status ?? "").toLowerCase()] ?? "neutral";
}

export function formatDateTime(value) {
  const date = value ? new Date(value) : null;
  if (!date || Number.isNaN(date.getTime())) return "";
  return date.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

export function isPastIso(value) {
  const date = value ? new Date(value) : null;
  if (!date || Number.isNaN(date.getTime())) return false;
  return date.getTime() < Date.now();
}

export function formatDuration(minutes) {
  const value = Number(minutes);
  if (!Number.isFinite(value) || value <= 0) return "";
  if (value < 60) return `${value} min`;
  const hours = Math.floor(value / 60);
  const rest = value % 60;
  return rest ? `${hours} h ${rest} min` : `${hours} h`;
}

export function personOf(field) {
  if (!field) return null;
  if (typeof field === "object") return field;
  if (typeof field === "string" && field.trim()) return { display_name: field };
  return null;
}

export function mentorName(mentor) {
  return (
    personOf(mentor?.user)?.display_name ||
    personOf(mentor?.user)?.username ||
    mentor?.display_name ||
    mentor?.name ||
    "CodeHer mentor"
  );
}

/** Shape for the Avatar/UserCell primitives from either a mentor record or a bare user object. */
export function mentorAvatarUser(mentor) {
  const user = personOf(mentor?.user);
  return {
    ...(user ?? {}),
    display_name: mentorName(mentor),
    avatar: mentor?.avatar ?? user?.avatar ?? "",
  };
}

export function topExpertise(mentors, limit = 12) {
  const counts = new Map();
  for (const mentor of mentors) {
    for (const value of mentor?.expertise ?? []) {
      const label = typeof value === "string" ? value : value?.name;
      if (!label) continue;
      counts.set(label, (counts.get(label) ?? 0) + 1);
    }
  }
  return [...counts.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, limit)
    .map(([label]) => label);
}

/** A preferred slot may arrive as a string or as { weekday, time } — render both honestly. */
export function slotLabel(slot) {
  if (!slot) return "";
  if (typeof slot === "string") return slot;
  const weekday = slot.weekday ?? slot.day ?? "";
  const time = slot.time ?? slot.starts_at ?? slot.datetime ?? "";
  const prettyDay = weekday ? weekday.charAt(0).toUpperCase() + weekday.slice(1) : "";
  return [prettyDay, time].filter(Boolean).join(" · ");
}

export function mentorIdOf(request) {
  const raw = request?.mentor ?? request?.mentor_id ?? null;
  if (raw && typeof raw === "object") return raw.id ?? raw.user ?? null;
  return raw;
}

export function learnerOf(request) {
  return personOf(request?.learner) ?? personOf(request?.user) ?? personOf(request?.student) ?? null;
}

export function mentorOf(request) {
  return personOf(request?.mentor) ?? personOf(request?.mentor_profile) ?? null;
}

export function statusOf(entity, fallback = "pending") {
  const value = String(entity?.status ?? entity?.state ?? "").toLowerCase();
  return value || fallback;
}

export function requestIdOf(value) {
  if (value && typeof value === "object") return value.id ?? null;
  return value ?? null;
}
