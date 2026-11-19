import { useCallback, useState } from "react";
import { Alert, Button, Field, Modal, Select, Textarea } from "../../components/ui";
import { api } from "../../services/api";

/** Feed/gallery page size. The API caps page_size at 50. */
export const PAGE_SIZE = 12;

/** Accepts a DRF page object or a bare list — the contract allows either for some endpoints. */
export function itemsFrom(payload) {
  if (Array.isArray(payload)) return payload;
  return payload?.results ?? [];
}

export function errorText(err) {
  if (!err) return "Unexpected error.";
  return err.detail || err.messageFor?.("__default__") || err.message || "Unexpected error.";
}

export function excerpt(text, max = 190) {
  const clean = String(text ?? "").replace(/\s+/g, " ").trim();
  if (!clean) return "";
  if (clean.length <= max) return clean;
  return `${clean.slice(0, max - 1).trimEnd()}…`;
}

export function timeAgo(value) {
  const date = value ? new Date(value) : null;
  if (!date || Number.isNaN(date.getTime())) return "";
  const seconds = Math.round((Date.now() - date.getTime()) / 1000);
  if (seconds < 0) return date.toLocaleDateString();
  if (seconds < 60) return "just now";
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours} h ago`;
  const days = Math.round(hours / 24);
  if (days < 14) return `${days} d ago`;
  return date.toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });
}

/** Serializers may expose the author as author/user/owner/creator, as an object or a plain name. */
export function authorOf(item) {
  if (!item) return null;
  const raw = item.author ?? item.user ?? item.owner ?? item.creator ?? null;
  if (raw && typeof raw === "object") return raw;
  if (typeof raw === "string" && raw.trim()) return { display_name: raw };
  return null;
}

export function isLiked(item) {
  return Boolean(item?.liked ?? item?.is_liked);
}

export function isBookmarked(item) {
  return Boolean(item?.bookmarked ?? item?.is_bookmarked);
}

export function likesCount(item) {
  return Number(item?.likes_count ?? item?.like_count ?? 0);
}

export function commentsCount(item) {
  return Number(item?.comments_count ?? item?.comment_count ?? 0);
}

export function bookmarksCount(item) {
  return Number(item?.bookmarks_count ?? item?.bookmark_count ?? 0);
}

function patchToggle(item, kind, result) {
  if (kind === "like") {
    const liked = result ? Boolean(result.liked ?? result.is_liked) : !isLiked(item);
    const count = Number(result?.likes_count ?? Math.max(0, likesCount(item) + (liked ? 1 : -1)));
    return { ...item, liked, likes_count: count };
  }
  const bookmarked = result ? Boolean(result.bookmarked ?? result.is_bookmarked) : !isBookmarked(item);
  const count = Number(
    result?.bookmarks_count ?? result?.bookmark_count ?? Math.max(0, bookmarksCount(item) + (bookmarked ? 1 : -1))
  );
  return { ...item, bookmarked, bookmarks_count: count };
}

/**
 * Optimistic like/bookmark toggles against `POST /community/{scope}/{id}/{kind}/`.
 * `mutate(id, updater)` applies an item change wherever the page stores it and is owned by the caller
 * (list page vs detail object), which is why it is injected rather than guessed here.
 */
export function useEngagement({ mutate, toast, scope = "posts" }) {
  const [pending, setPending] = useState({});

  const run = useCallback(
    async (item, kind) => {
      const snapshot = item;
      const key = `${item.id}:${kind}`;
      mutate(item.id, (current) => patchToggle(current ?? snapshot, kind));
      setPending((map) => ({ ...map, [key]: true }));
      try {
        const result = await api.post(`/community/${scope}/${item.id}/${kind}/`, {});
        mutate(item.id, (current) => patchToggle(current ?? snapshot, kind, result));
      } catch (err) {
        mutate(item.id, () => snapshot);
        toast.error(errorText(err));
      } finally {
        setPending((map) => {
          const next = { ...map };
          delete next[key];
          return next;
        });
      }
    },
    [mutate, scope, toast]
  );

  const isPending = useCallback((id, kind) => Boolean(pending[`${id}:${kind}`]), [pending]);

  return { run, isPending };
}

function collectLabels(items, key, limit) {
  const counts = new Map();
  for (const item of items) {
    for (const value of item?.[key] ?? []) {
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

/** Filter chips are derived from real rows currently loaded — never invented. */
export function topTags(items, limit = 12) {
  return collectLabels(items, "tags", limit);
}

export function topTechnologies(items, limit = 12) {
  return collectLabels(items, "technologies", limit);
}

function hashString(value) {
  let h = 2166136261;
  for (let i = 0; i < value.length; i += 1) {
    h ^= value.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return Math.abs(h);
}

export function gradientFor(seed) {
  const h = hashString(String(seed || "codeher"));
  const a = h % 360;
  const b = (a + 80 + (h % 70)) % 360;
  return `linear-gradient(135deg, hsl(${a} 70% 46%), hsl(${b} 72% 26%))`;
}

/** Screenshot with alt text; falls back to a generated gradient cover — never a broken image. */
export function ProjectThumb({ project, className = "" }) {
  const [failed, setFailed] = useState(false);
  const src = project?.screenshot ?? project?.screenshot_url ?? "";
  const title = project?.title ?? "Project";

  if (src && !failed) {
    return (
      <img
        className={`proj-thumb ${className}`.trim()}
        src={src}
        alt={`${title} — screenshot`}
        loading="lazy"
        onError={() => setFailed(true)}
      />
    );
  }
  return (
    <div
      className={`proj-thumb proj-thumb--placeholder ${className}`.trim()}
      style={{ background: gradientFor(title) }}
      role="img"
      aria-label={`${title} — no screenshot available, generated cover`}
    >
      <span className="proj-thumb__label">{title}</span>
    </div>
  );
}

const REPORT_REASONS = [
  { value: "spam", label: "Spam or advertising" },
  { value: "harassment", label: "Harassment or unkind behaviour" },
  { value: "inappropriate", label: "Inappropriate content" },
  { value: "off_topic", label: "Off topic for CodeHer" },
  { value: "other", label: "Something else" },
];

/** Shared report dialog for posts and projects — POST /community/{scope}/{id}/report/. */
export function ReportModal({ open, onClose, scope, target, toast }) {
  const [reason, setReason] = useState("spam");
  const [details, setDetails] = useState("");
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState(null);

  const submit = async () => {
    setBusy(true);
    setFailure(null);
    try {
      await api.post(`/community/${scope}/${target.id}/report/`, { reason, details });
      toast?.success("Report submitted — a moderator will review it.");
      setDetails("");
      onClose?.();
    } catch (err) {
      setFailure(err);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={`Report this ${scope === "posts" ? "post" : "project"}`}
      description="Reports go to CodeHer moderators. Tell us what is wrong and we will look."
      footer={
        <>
          <Button variant="ghost" onClick={onClose} disabled={busy}>
            Cancel
          </Button>
          <Button variant="danger" onClick={submit} loading={busy}>
            Submit report
          </Button>
        </>
      }
    >
      <div className="form-grid">
        <Field label="Reason" required htmlFor="report-reason">
          <Select
            id="report-reason"
            data-autofocus
            value={reason}
            onChange={(event) => setReason(event.target.value)}
            options={REPORT_REASONS}
          />
        </Field>
        <Field label="Details (optional)" htmlFor="report-details">
          <Textarea
            id="report-details"
            rows={4}
            value={details}
            onChange={(event) => setDetails(event.target.value)}
            placeholder="Anything the moderators should know?"
          />
        </Field>
        {failure && <Alert variant="error">{errorText(failure)}</Alert>}
      </div>
    </Modal>
  );
}
