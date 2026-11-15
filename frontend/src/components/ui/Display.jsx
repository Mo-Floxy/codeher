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

function initials(name = "") {
  const parts = String(name).trim().split(/\s+/).filter(Boolean);
  if (!parts.length) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

export function Avatar({ user, size = "md", className = "" }) {
  const name = user?.display_name || user?.username || user?.email || "";
  const src = user?.avatar;
  const sizes = { sm: "avatar--sm", lg: "avatar--lg", xl: "avatar--xl" };
  return (
    <span className={`avatar ${sizes[size] ?? ""} ${className}`.trim()} aria-hidden={!name || undefined} title={name || undefined}>
      {src ? <img src={src} alt={name ? `${name} avatar` : "User avatar"} /> : initials(name)}
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
