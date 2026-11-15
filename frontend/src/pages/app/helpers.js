// Shared formatting + normalisation helpers for the CodeHer app + admin pages.
// Kept small and pure so every page can lean on them without duplicating logic.

/** Normalise a DRF paginated list or a bare array into an array. */
export function asList(payload) {
  if (!payload) return [];
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload.results)) return payload.results;
  return [];
}

/** Coerce anything numeric-ish to a finite number, else 0. */
export function num(value, fallback = 0) {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

export function sum(list, key) {
  return list.reduce((total, item) => total + num(typeof key === "function" ? key(item) : item?.[key]), 0);
}

// ---- Date keys are handled as plain YYYY-MM-DD strings so timezone offsets
// ---- never shift a day, which matters for the streak heat strip.
export function todayKey() {
  const now = new Date();
  return toKey(now.getFullYear(), now.getMonth() + 1, now.getDate());
}

function toKey(year, month, day) {
  return `${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}

export function dateKeyPart(value) {
  if (!value) return null;
  const text = String(value).slice(0, 10);
  return /^\d{4}-\d{2}-\d{2}$/.test(text) ? text : null;
}

/** Shift a YYYY-MM-DD key by `days` without leaving UTC midnight. */
export function shiftDateKey(key, days) {
  const [year, month, day] = key.split("-").map(Number);
  const date = new Date(Date.UTC(year, month - 1, day));
  date.setUTCDate(date.getUTCDate() + days);
  return toKey(date.getUTCFullYear(), date.getUTCMonth() + 1, date.getUTCDate());
}

/** Build an inclusive array of the last `count` date keys ending at `endKey`. */
export function recentDateKeys(endKey, count) {
  const end = dateKeyPart(endKey) ?? todayKey();
  const keys = [];
  for (let offset = count - 1; offset >= 0; offset -= 1) keys.push(shiftDateKey(end, -offset));
  return keys;
}

/** "Mon 12" style label for chart axes derived from a date key/ISO value. */
export function shortDayLabel(value) {
  const key = dateKeyPart(value);
  if (key) {
    const [year, month, day] = key.split("-").map(Number);
    const date = new Date(Date.UTC(year, month - 1, day));
    return date.toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric", timeZone: "UTC" });
  }
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? String(value)
    : date.toLocaleDateString(undefined, { weekday: "short", day: "numeric", month: "short" });
}

export function formatDate(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value).slice(0, 10);
  return date.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

/** Human relative time, e.g. "3 hours ago". Falls back to a date for old items. */
export function formatRelative(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  const diff = date.getTime() - Date.now();
  const abs = Math.abs(diff);
  const future = diff > 0;
  const units = [
    ["second", 1000],
    ["minute", 60000],
    ["hour", 3600000],
    ["day", 86400000],
    ["week", 604800000],
    ["month", 2592000000],
    ["year", 31536000000],
  ];
  if (abs < 45000) return future ? "in a moment" : "just now";
  for (let i = units.length - 1; i >= 0; i -= 1) {
    const [name, ms] = units[i];
    if (abs >= ms) {
      const amount = Math.round(abs / ms);
      const label = `${amount} ${name}${amount === 1 ? "" : "s"}`;
      return future ? `in ${label}` : `${label} ago`;
    }
  }
  return formatDate(value);
}

/** Resolve a possibly-nested reference (id | object) into an id + label. */
export function resolveRef(ref) {
  if (ref == null) return { id: null, label: "" };
  if (typeof ref === "object") {
    const id = ref.id ?? ref.slug ?? null;
    const label = ref.title ?? ref.display_name ?? ref.name ?? ref.username ?? (id != null ? `#${id}` : "");
    return { id, label };
  }
  return { id: ref, label: `#${ref}` };
}
