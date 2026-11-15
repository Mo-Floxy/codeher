import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Link } from "react-router-dom";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { X } from "lucide-react";
import { useDismiss } from "../../hooks";
import { Button } from "./Button";

export function Modal({ open, onClose, title, description, children, footer, wide }) {
  const reduce = useReducedMotion();
  const panelRef = useRef(null);

  useEffect(() => {
    if (!open) return undefined;
    const onKeyDown = (event) => {
      if (event.key === "Escape") onClose?.();
    };
    document.addEventListener("keydown", onKeyDown);
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    // Move focus into the dialog, restore it to the trigger afterwards.
    const opener = document.activeElement;
    const target = panelRef.current?.querySelector("[data-autofocus]") ?? panelRef.current;
    target?.focus?.();
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.body.style.overflow = previousOverflow;
      if (opener?.focus) opener.focus();
    };
  }, [open, onClose]);

  return createPortal(
    <AnimatePresence>
      {open && (
        <motion.div
          className="modal-backdrop"
          initial={reduce ? false : { opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.18 }}
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) onClose?.();
          }}
        >
          <motion.div
            ref={panelRef}
            className={`modal ${wide ? "modal--wide" : ""}`.trim()}
            role="dialog"
            aria-modal="true"
            aria-label={title ?? "Dialog"}
            tabIndex={-1}
            initial={reduce ? false : { opacity: 0, y: 22, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={reduce ? { opacity: 0 } : { opacity: 0, y: 12, scale: 0.98 }}
            transition={{ duration: 0.26, ease: [0.22, 1, 0.36, 1] }}
          >
            <button type="button" className="modal__close" onClick={onClose} aria-label="Close dialog">
              <X size={18} />
            </button>
            {(title || description) && (
              <header className="modal__head">
                {title && <h3>{title}</h3>}
                {description && <p style={{ fontSize: "var(--fs-sm)" }}>{description}</p>}
              </header>
            )}
            {children}
            {footer && <footer className="modal__foot">{footer}</footer>}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>,
    document.body
  );
}

export function ConfirmDialog({ open, onClose, onConfirm, title, message, confirmLabel = "Confirm", variant = "danger", busy }) {
  return (
    <Modal
      open={open}
      onClose={onClose}
      title={title}
      description={message}
      footer={
        <>
          <Button variant="ghost" onClick={onClose} disabled={busy}>
            Cancel
          </Button>
          <Button variant={variant} onClick={onConfirm} loading={busy}>
            {confirmLabel}
          </Button>
        </>
      }
    />
  );
}

export function Dropdown({ trigger, children, align = "right", open, onOpenChange }) {
  const [internalOpen, setInternalOpen] = useState(false);
  const isOpen = open ?? internalOpen;
  const setOpen = onOpenChange ?? setInternalOpen;
  const ref = useDismiss(isOpen, () => setOpen(false));
  const reduce = useReducedMotion();

  return (
    <span ref={ref} style={{ position: "relative", display: "inline-flex" }}>
      {typeof trigger === "function" ? trigger(isOpen) : trigger}
      <AnimatePresence>
        {isOpen && (
          <motion.span
            className="dropdown"
            style={{ display: "grid", gap: 2, ...(align === "left" ? { right: "auto", left: 0 } : {}) }}
            initial={reduce ? false : { opacity: 0, y: -6, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -4, scale: 0.98 }}
            transition={{ duration: 0.16 }}
          >
            {children}
          </motion.span>
        )}
      </AnimatePresence>
    </span>
  );
}

export function DropdownItem({ children, onClick, to, danger, icon: Icon, ...rest }) {
  const classes = `dropdown__item ${danger ? "dropdown__item--danger" : ""}`.trim();
  if (to) {
    return (
      <Link to={to} className={classes} onClick={onClick} {...rest}>
        {children}
      </Link>
    );
  }
  return (
    <button type="button" className={classes} onClick={onClick} {...rest}>
      {Icon && <Icon size={16} aria-hidden="true" />}
      {children}
    </button>
  );
}
