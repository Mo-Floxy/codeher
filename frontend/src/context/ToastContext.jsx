import { createContext, useCallback, useContext, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { CheckCircle2, Info, TriangleAlert, X, XCircle } from "lucide-react";
import { useReducedMotion } from "framer-motion";

const ToastContext = createContext(null);

const ICONS = {
  success: CheckCircle2,
  error: XCircle,
  warning: TriangleAlert,
  info: Info,
};

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const timers = useRef(new Map());

  const dismiss = useCallback((id) => {
    setToasts((current) => current.filter((toast) => toast.id !== id));
    const timer = timers.current.get(id);
    if (timer) {
      clearTimeout(timer);
      timers.current.delete(id);
    }
  }, []);

  const push = useCallback(
    (message, { variant = "info", title, duration = 4200 } = {}) => {
      if (!message) return null;
      const id = `t${Date.now()}${Math.random().toString(16).slice(2, 7)}`;
      setToasts((current) => [...current.slice(-3), { id, message, variant, title }]);
      const timer = setTimeout(() => dismiss(id), duration);
      timers.current.set(id, timer);
      return id;
    },
    [dismiss]
  );

  const value = useMemo(
    () => ({
      push,
      dismiss,
      success: (message, options) => push(message, { ...options, variant: "success" }),
      error: (message, options) => push(message, { ...options, variant: "error", duration: 6000 }),
      warning: (message, options) => push(message, { ...options, variant: "warning" }),
      info: (message, options) => push(message, { ...options, variant: "info" }),
    }),
    [push, dismiss]
  );

  const reduce = useReducedMotion();

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="toast-stack" role="region" aria-live="polite" aria-label="Notifications">
        <AnimatePresence>
          {toasts.map((toast) => {
            const Icon = ICONS[toast.variant] ?? Info;
            return (
              <motion.div
                key={toast.id}
                layout={!reduce}
                className={`toast toast--${toast.variant}`}
                initial={reduce ? false : { opacity: 0, y: 18, scale: 0.96 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 10, scale: 0.97 }}
                transition={{ duration: 0.24, ease: [0.22, 1, 0.36, 1] }}
              >
                <Icon className="toast__icon" size={19} aria-hidden="true" />
                <div style={{ flex: 1, minWidth: 0 }}>
                  {toast.title && (
                    <strong style={{ display: "block", fontSize: "var(--fs-sm)" }}>{toast.title}</strong>
                  )}
                  <span style={{ color: "var(--text-secondary)" }}>{toast.message}</span>
                </div>
                <button
                  type="button"
                  className="modal__close"
                  style={{ position: "static", width: 26, height: 26 }}
                  onClick={() => dismiss(toast.id)}
                  aria-label="Dismiss notification"
                >
                  <X size={15} />
                </button>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used inside <ToastProvider>");
  return ctx;
}
