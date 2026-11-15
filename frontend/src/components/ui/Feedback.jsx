import { AlertTriangle, Loader2, RefreshCw, SearchX } from "lucide-react";
import { Button } from "./Button";

export function Skeleton({ className = "", style, ...rest }) {
  return <div className={`skeleton ${className}`.trim()} style={style} aria-hidden="true" {...rest} />;
}

export function SkeletonText({ lines = 3, width }) {
  return (
    <div className="stack" style={{ gap: "var(--sp-2)" }}>
      {Array.from({ length: lines }).map((_, index) => (
        <Skeleton
          key={index}
          className="skeleton--text"
          style={{ width: index === lines - 1 ? "62%" : (width ?? "100%") }}
        />
      ))}
    </div>
  );
}

export function SkeletonCard({ height = 200 }) {
  return <Skeleton className="skeleton--card" style={{ height }} />;
}

export function SkeletonList({ count = 6, height = 200 }) {
  return (
    <div className="grid-auto">
      {Array.from({ length: count }).map((_, index) => (
        <SkeletonCard key={index} height={height} />
      ))}
    </div>
  );
}

export function Loading({ label = "Loading", className = "" }) {
  return (
    <div className={`row ${className}`.trim()} style={{ justifyContent: "center", gap: "var(--sp-2)", padding: "var(--sp-4) 0" }} role="status">
      <Loader2 size={17} className="spin" aria-hidden="true" />
      <span className="muted">{label}…</span>
    </div>
  );
}

export function EmptyState({ icon: Icon = SearchX, title, description, action, children }) {
  return (
    <div className="empty-state">
      <span className="empty-state__icon">
        <Icon size={26} aria-hidden="true" />
      </span>
      <h4>{title}</h4>
      {description && <p style={{ maxWidth: "52ch" }}>{description}</p>}
      {action}
      {children}
    </div>
  );
}

/** Renders the error with a retry affordance — never a silent blank screen. */
export function ErrorState({ error, onRetry, title = "We could not load this" }) {
  const message =
    error?.detail || error?.message || "Unexpected error. Please try again.";
  return (
    <EmptyState icon={AlertTriangle} title={title} description={message} action={
      onRetry ? (
        <Button variant="ghost" size="sm" onClick={onRetry}>
          <RefreshCw size={15} /> Try again
        </Button>
      ) : null
    } />
  );
}

export function Alert({ variant = "info", title, children, onDismiss }) {
  const Icon = variant === "success" ? Loader2 : AlertTriangle;
  return (
    <div className={`alert alert--${variant}`} role={variant === "error" ? "alert" : "status"}>
      {variant !== "info" && <Icon size={17} style={{ flex: "0 0 auto", marginTop: 2 }} aria-hidden="true" />}
      <div style={{ flex: 1 }}>
        {title && <strong style={{ display: "block", marginBottom: 2 }}>{title}</strong>}
        <span>{children}</span>
      </div>
      {onDismiss && (
        <button type="button" onClick={onDismiss} aria-label="Dismiss" style={{ color: "inherit" }}>
          ×
        </button>
      )}
    </div>
  );
}

export function ProgressBar({ value = 0, label, showValue, thin, variant, format }) {
  const clamped = Math.max(0, Math.min(100, Math.round(value ?? 0)));
  return (
    <div className="stack" style={{ gap: 6 }}>
      {(label || showValue) && (
        <div className="row" style={{ justifyContent: "space-between", width: "100%" }}>
          {label && <span className="muted" style={{ fontSize: "var(--fs-xs)", fontWeight: 700 }}>{label}</span>}
          {showValue && (
            <span style={{ fontSize: "var(--fs-xs)", fontWeight: 800, color: "var(--text-secondary)" }}>
              {format ? format(clamped) : `${clamped}%`}
            </span>
          )}
        </div>
      )}
      <div
        className={`progress ${thin ? "progress--thin" : ""} ${variant ? `progress--${variant}` : ""}`.trim()}
        role="progressbar"
        aria-valuenow={clamped}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={label ?? "Progress"}
      >
        <div className="progress__bar" style={{ width: `${clamped}%` }} />
      </div>
    </div>
  );
}
