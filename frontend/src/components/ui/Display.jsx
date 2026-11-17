import { useId } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Link } from "react-router-dom";

export function Badge({ variant = "neutral", children, className = "" }) {
  return <span className={`badge badge--${variant} ${className}`.trim()}>{children}</span>;
}

/** Skill levels map to one colour everywhere: beginner green, intermediate amber, advanced rose. */
export function LevelBadge({ level }) {
  if (!level) return null;
  const key = String(level).toLowerCase();
  const variant = key.startsWith("begin") ? "beginner" : key.startsWith("inter") ? "intermediate" : key ? "advanced" : "neutral";
  return <Badge variant={variant}>{level}</Badge>;
}

export function Chip({ children, selected, onClick, as, to, className = "", ...rest }) {
  const classes = `chip ${onClick || to ? "chip--button" : ""} ${selected ? "chip--active" : ""} ${className}`.trim();
  if (to) {
    return (
      <Link to={to} className={classes} {...rest}>
        {children}
      </Link>
    );
  }
  const Tag = as ?? (onClick ? "button" : "span");
  return (
    <Tag
      className={classes}
      type={Tag === "button" ? "button" : undefined}
      onClick={onClick}
      aria-pressed={onClick ? Boolean(selected) : undefined}
      {...rest}
    >
      {children}
    </Tag>
  );
}

export function ChipRow({ children, className = "" }) {
  return (
    <div className={`row ${className}`.trim()} style={{ gap: "var(--sp-2)" }}>
      {children}
    </div>
  );
}

/** Gradient pairs kept inside the brand palette: violet, purple, pink, cyan, indigo. */
const AVATAR_PALETTE = [
  ["#8b5cf6", "#ec4899"],
  ["#22d3ee", "#6366f1"],
  ["#f472b6", "#7c3aed"],
  ["#6366f1", "#14b8a6"],
  ["#a855f7", "#38bdf8"],
  ["#e879f9", "#4f46e5"],
];

const AVATAR_ANCHORS = [
  [22, 22],
  [43, 24],
  [23, 43],
  [42, 42],
];

/** FNV-1a over the member's stable identifier, so the same person always paints the
 * same picture across the app and no seed text can leak into the markup. */
function hash32(value) {
  let hash = 2166136261;
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index);
    hash = Math.imul(hash, 16777619) >>> 0;
  }
  return hash >>> 0;
}

/** Abstract artwork for members without a photo — deliberately not a drawn face, so it
 * never reads as a stand-in portrait of a real person.
 *
 * Every bit extraction below uses `>>>`, not `>>`: hash32 returns an unsigned 32-bit
 * value, and a signed shift turns the upper half of that range negative, so
 * `(hash >> 4) % 4` can be -3 and index the palette arrays out of bounds. */
function GeneratedAvatar({ seed, label }) {
  const gradientId = useId();
  const hash = hash32(seed);
  const [from, to] = AVATAR_PALETTE[hash % AVATAR_PALETTE.length];
  const anchor = (hash >>> 4) % AVATAR_ANCHORS.length;
  const light = AVATAR_ANCHORS[anchor];
  const dark = AVATAR_ANCHORS[(anchor + 2) % AVATAR_ANCHORS.length];

  return (
    <svg
      className="avatar__art"
      viewBox="0 0 64 64"
      role="img"
      aria-label={label}
      preserveAspectRatio="xMidYMid slice"
    >
      <defs>
        <linearGradient id={gradientId} x1="0" y1="0" x2="1" y2="1" gradientTransform={`rotate(${((hash >>> 8) % 4) * 45} 0.5 0.5)`}>
          <stop offset="0" stopColor={from} />
          <stop offset="1" stopColor={to} />
        </linearGradient>
      </defs>
      <rect width="64" height="64" fill={`url(#${gradientId})`} />
      <circle cx={dark[0]} cy={dark[1]} r={13 + ((hash >>> 12) % 4)} fill="#0b0a1e" fillOpacity="0.22" />
      <circle cx={light[0]} cy={light[1]} r={18 + ((hash >>> 6) % 5)} fill="#ffffff" fillOpacity="0.2" />
      <circle
        cx="32"
        cy={28 + ((hash >>> 16) % 9)}
        r={26 + ((hash >>> 20) % 5)}
        fill="none"
        stroke="#ffffff"
        strokeOpacity="0.3"
        strokeWidth={2 + ((hash >>> 24) % 3)}
      />
    </svg>
  );
}

export function Avatar({ user, size = "md", className = "" }) {
  const name = user?.display_name || user?.username || user?.email || "";
  const src = user?.avatar;
  const seed = String(user?.id ?? user?.pk ?? user?.username ?? user?.email ?? name);
  const sizes = { sm: "avatar--sm", lg: "avatar--lg", xl: "avatar--xl" };
  return (
    <span className={`avatar ${sizes[size] ?? ""} ${className}`.trim()} aria-hidden={!name || undefined} title={name || undefined}>
      {src ? (
        <img src={src} alt={name ? `${name} avatar` : "User avatar"} />
      ) : (
        <GeneratedAvatar seed={seed} label={name ? `${name} avatar` : "Member avatar"} />
      )}
    </span>
  );
}

export function UserCell({ user, to, subtitle, size = "sm" }) {
  const content = (
    <>
      <Avatar user={user} size={size} />
      <span style={{ minWidth: 0 }}>
        <span style={{ display: "block", fontWeight: 700, color: "var(--text-primary)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {user?.display_name || user?.username || "Member"}
        </span>
        {subtitle && <span className="muted" style={{ fontSize: "var(--fs-xs)" }}>{subtitle}</span>}
      </span>
    </>
  );
  if (to) {
    return (
      <Link to={to} className="row" style={{ gap: "var(--sp-2)", color: "inherit" }}>
        {content}
      </Link>
    );
  }
  return <span className="row" style={{ gap: "var(--sp-2)" }}>{content}</span>;
}

/** Accessible tablist; `items` is [{ value, label, count }]. */
export function Tabs({ items, value, onChange, ariaLabel = "Tabs", className = "" }) {
  return (
    <div className={`tabs ${className}`.trim()} role="tablist" aria-label={ariaLabel}>
      {items.map((item) => (
        <button
          key={item.value}
          role="tab"
          type="button"
          className="tab"
          aria-selected={value === item.value}
          onClick={() => onChange(item.value)}
        >
          {item.label}
          {item.count != null && <span style={{ marginLeft: 6, opacity: 0.75 }}>({item.count})</span>}
        </button>
      ))}
    </div>
  );
}

/** DRF page-based pagination: pass { count, page, page_size } plus setPage. */
export function Pagination({ count = 0, page = 1, pageSize = 12, onPageChange }) {
  const pages = Math.max(1, Math.ceil(count / pageSize));
  if (pages <= 1) return null;

  const window = [];
  const from = Math.max(1, Math.min(page - 2, pages - 4));
  for (let index = from; index <= Math.min(pages, from + 4); index += 1) window.push(index);

  return (
    <nav className="pagination" aria-label="Pagination">
      <button className="pagination__page" onClick={() => onPageChange(page - 1)} disabled={page <= 1} aria-label="Previous page">
        <ChevronLeft size={16} />
      </button>
      {from > 1 && <span className="muted" style={{ padding: "0 4px" }}>…</span>}
      {window.map((index) => (
        <button
          key={index}
          className="pagination__page"
          onClick={() => onPageChange(index)}
          aria-current={index === page ? "page" : undefined}
          aria-label={`Page ${index}`}
        >
          {index}
        </button>
      ))}
      {from + 4 < pages && <span className="muted" style={{ padding: "0 4px" }}>…</span>}
      <button className="pagination__page" onClick={() => onPageChange(page + 1)} disabled={page >= pages} aria-label="Next page">
        <ChevronRight size={16} />
      </button>
    </nav>
  );
}

export function SectionHeading({ eyebrow, title, description, center, action }) {
  return (
    <header className={`section-head ${center ? "section-head--center" : ""}`.trim()}>
      {eyebrow && <span className="eyebrow">{eyebrow}</span>}
      <h2>{title}</h2>
      {description && <p className="lead">{description}</p>}
      {action}
    </header>
  );
}
