import { forwardRef, useId } from "react";
import { Eye, EyeOff, Search } from "lucide-react";
import { useState } from "react";

export function Field({ label, hint, error, required, htmlFor, children, className = "" }) {
  const id = useId();
  const targetId = htmlFor ?? id;
  return (
    <div className={`field ${error ? "field--invalid" : ""} ${className}`.trim()}>
      {label && (
        <label className="field__label" htmlFor={targetId}>
          {label}
          {required && <span aria-hidden="true"> *</span>}
        </label>
      )}
      {children}
      {error ? (
        <p className="field__error" role="alert" id={`${targetId}-error`}>
          {error}
        </p>
      ) : hint ? (
        <p className="field__hint" id={`${targetId}-hint`}>
          {hint}
        </p>
      ) : null}
    </div>
  );
}

const describedBy = (error, hint) => (error || hint ? true : undefined);

export const Input = forwardRef(function Input({ error, hint, icon, ...rest }, ref) {
  return (
    <input
      ref={ref}
      className="input"
      aria-invalid={error ? "true" : undefined}
      aria-describedby={describedBy(error, hint) ? undefined : undefined}
      {...rest}
    />
  );
});

export const Textarea = forwardRef(function Textarea({ error, rows = 5, ...rest }, ref) {
  return (
    <textarea ref={ref} rows={rows} className="textarea" aria-invalid={error ? "true" : undefined} {...rest} />
  );
});

export const Select = forwardRef(function Select({ error, options = [], children, ...rest }, ref) {
  return (
    <select ref={ref} className="select" aria-invalid={error ? "true" : undefined} {...rest}>
      {options.map((option) => (
        <option key={option.value ?? option} value={option.value ?? option}>
          {option.label ?? option}
        </option>
      ))}
      {children}
    </select>
  );
});

export function SearchInput({ label = "Search", value, onChange, placeholder = "Search…", ...rest }) {
  return (
    <div className="input-group">
      <span className="input-group__icon" aria-hidden="true">
        <Search size={17} />
      </span>
      <input
        type="search"
        className="input"
        value={value}
        onChange={(event) => onChange?.(event.target.value)}
        placeholder={placeholder}
        aria-label={label}
        {...rest}
      />
    </div>
  );
}

export function PasswordInput({ error, ...rest }) {
  const [visible, setVisible] = useState(false);
  return (
    <div className="input-group">
      <input
        type={visible ? "text" : "password"}
        className="input"
        aria-invalid={error ? "true" : undefined}
        style={{ paddingRight: 44 }}
        {...rest}
      />
      <button
        type="button"
        className="input-group__action"
        onClick={() => setVisible((current) => !current)}
        aria-label={visible ? "Hide password" : "Show password"}
        aria-pressed={visible}
      >
        {visible ? <EyeOff size={17} /> : <Eye size={17} />}
      </button>
    </div>
  );
}

export function Checkbox({ label, description, id, ...rest }) {
  const autoId = useId();
  const controlId = id ?? autoId;
  return (
    <label className="checkbox" htmlFor={controlId}>
      <input id={controlId} type="checkbox" {...rest} />
      <span>
        {label}
        {description && <span className="field__hint" style={{ display: "block" }}>{description}</span>}
      </span>
    </label>
  );
}

export function Switch({ checked, onChange, label, id, ...rest }) {
  const autoId = useId();
  const controlId = id ?? autoId;
  return (
    <label className="checkbox" htmlFor={controlId}>
      <span
        id={controlId}
        role="switch"
        tabIndex={0}
        aria-checked={Boolean(checked)}
        className="switch"
        onClick={() => onChange?.(!checked)}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            onChange?.(!checked);
          }
        }}
        {...rest}
      />
      <span>{label}</span>
    </label>
  );
}

/** Pill list with free-text entry — used for interests, technologies and tags. */
export function TagInput({ label, value = [], onChange, placeholder = "Add and press Enter", max = 12 }) {
  const [draft, setDraft] = useState("");
  const add = () => {
    const next = draft.trim().replace(/,$/, "");
    if (!next || value.includes(next) || value.length >= max) {
      setDraft("");
      return;
    }
    onChange?.([...value, next]);
    setDraft("");
  };
  return (
    <div className="field">
      {label && <span className="field__label">{label}</span>}
      <div className="row" style={{ gap: "var(--sp-2)" }}>
        {value.map((tag) => (
          <span key={tag} className="chip">
            {tag}
            <button
              type="button"
              onClick={() => onChange?.(value.filter((item) => item !== tag))}
              aria-label={`Remove ${tag}`}
              style={{ color: "var(--danger)", display: "flex" }}
            >
              ×
            </button>
          </span>
        ))}
      </div>
      <input
        className="input"
        value={draft}
        placeholder={placeholder}
        onChange={(event) => setDraft(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === ",") {
            event.preventDefault();
            add();
          } else if (event.key === "Backspace" && !draft && value.length) {
            onChange?.(value.slice(0, -1));
          }
        }}
        onBlur={add}
        aria-label={label ?? "Tags"}
      />
    </div>
  );
}
