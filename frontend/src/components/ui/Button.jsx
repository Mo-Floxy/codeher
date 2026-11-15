import { forwardRef } from "react";
import { Link } from "react-router-dom";

/** Renders an internal <Link>, an external <a>, or a <button> — one component, always keyboard-correct. */
export const Button = forwardRef(function Button(
  { as, to, href, variant = "primary", size, block, loading, className = "", type, children, ...rest },
  ref
) {
  const classes = ["btn", `btn--${variant}`, size && `btn--${size}`, block && "btn--block", className]
    .filter(Boolean)
    .join(" ");
  const isDisabled = Boolean(rest.disabled) || Boolean(loading);

  const content = loading ? (
    <>
      <span className="btn__spinner" aria-hidden="true" />
      {children}
    </>
  ) : (
    children
  );

  if (to) {
    return (
      <Link ref={ref} to={to} className={classes} aria-disabled={isDisabled || undefined} {...rest}>
        {content}
      </Link>
    );
  }

  if (href) {
    return (
      <a
        ref={ref}
        href={href}
        className={classes}
        target={rest.target ?? "_blank"}
        rel="noreferrer"
        aria-disabled={isDisabled || undefined}
        {...rest}
      >
        {content}
      </a>
    );
  }

  const Tag = as ?? "button";
  return (
    <Tag ref={ref} type={Tag === "button" ? (type ?? "button") : undefined} className={classes} disabled={isDisabled} {...rest}>
      {content}
    </Tag>
  );
});

export function IconButton({ label, children, variant = "ghost", ...rest }) {
  return (
    <Button variant={variant} className="btn--icon" aria-label={label} title={label} {...rest}>
      {children}
    </Button>
  );
}

export function ButtonGroup({ children, className = "", ...rest }) {
  return (
    <div className={`row ${className}`.trim()} {...rest}>
      {children}
    </div>
  );
}
