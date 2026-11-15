import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Check, UserPlus, X } from "lucide-react";
import AuthShell from "./AuthShell";
import { Alert, Button, Checkbox, Field, Input, PasswordInput } from "../../components/ui";
import { useAuth } from "../../context/AuthContext";
import { useToast } from "../../context/ToastContext";
import "./auth.css";

const RULES = [
  { key: "length", label: "At least 8 characters", test: (value) => value.length >= 8 },
  { key: "letters", label: "Contains a letter", test: (value) => /[A-Za-z]/.test(value) },
  { key: "digits", label: "Contains a number", test: (value) => /\d/.test(value) },
  { key: "match", label: "Both passwords match", test: (value, confirm) => Boolean(confirm) && value === confirm },
];

export default function SignUp() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const toast = useToast();
  const [form, setForm] = useState({ display_name: "", username: "", email: "", password: "", password2: "" });
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState("");
  const [busy, setBusy] = useState(false);
  const [accepted, setAccepted] = useState(false);

  const set = (key) => (event) => setForm((current) => ({ ...current, [key]: event.target.value }));

  const ruleState = useMemo(
    () => RULES.map((rule) => ({ ...rule, ok: rule.test(form.password, form.password2) })),
    [form.password, form.password2]
  );

  const validate = () => {
    const next = {};
    if (!form.display_name.trim()) next.display_name = "Tell us what to call you.";
    if (!/^[A-Za-z0-9_.-]{3,150}$/.test(form.username)) next.username = "3–150 characters: letters, numbers, . _ -";
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(form.email)) next.email = "Enter a valid email address.";
    if (!RULES.slice(0, 3).every((rule) => rule.test(form.password))) next.password = "Password does not meet the rules below.";
    if (form.password !== form.password2) next.password2 = "Passwords do not match.";
    if (!accepted) next.terms = "Please accept the community guidelines.";
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const submit = async (event) => {
    event.preventDefault();
    setFormError("");
    if (!validate()) return;
    setBusy(true);
    try {
      const { terms, ...payload } = form;
      const user = await register(payload);
      toast.success(`Your account is ready, ${user.display_name || user.username}.`);
      navigate("/dashboard", { replace: true });
    } catch (error) {
      setErrors(error.fieldErrors ?? {});
      setFormError(error.detail || "We could not create your account. Please fix the fields below.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthShell
      title="Create your account"
      subtitle="Free, and takes under two minutes. You will start on your first lesson immediately."
      wide
      footer={
        <>
          Already learning with CodeHer? <Link to="/signin">Sign in instead</Link>
        </>
      }
    >
      <form className="stack" style={{ gap: "var(--sp-4)" }} onSubmit={submit} noValidate>
        {formError && <Alert variant="error">{formError}</Alert>}

        <div className="form-grid form-grid--2">
          <Field label="Display name" error={errors.display_name} htmlFor="su-name" required>
            <Input id="su-name" value={form.display_name} onChange={set("display_name")} placeholder="Ada Lovelace" autoComplete="name" error={errors.display_name} required />
          </Field>
          <Field label="Username" error={errors.username} htmlFor="su-username" hint="Used in your member profile URL." required>
            <Input id="su-username" value={form.username} onChange={set("username")} placeholder="ada" autoComplete="username" error={errors.username} required />
          </Field>
        </div>

        <Field label="Email address" error={errors.email} htmlFor="su-email" required>
          <Input id="su-email" type="email" value={form.email} onChange={set("email")} placeholder="you@example.com" autoComplete="email" error={errors.email} required />
        </Field>

        <div className="form-grid form-grid--2">
          <Field label="Password" error={errors.password} htmlFor="su-password" required>
            <PasswordInput id="su-password" value={form.password} onChange={set("password")} placeholder="Choose a password" autoComplete="new-password" error={errors.password} required />
          </Field>
          <Field label="Confirm password" error={errors.password2} htmlFor="su-password2" required>
            <PasswordInput id="su-password2" value={form.password2} onChange={set("password2")} placeholder="Repeat it" autoComplete="new-password" error={errors.password2} required />
          </Field>
        </div>

        <ul className="password-rules" aria-label="Password requirements">
          {ruleState.map((rule) => (
            <li key={rule.key} data-ok={rule.ok}>
              {rule.ok ? <Check size={13} /> : <X size={13} />}
              {rule.label}
            </li>
          ))}
        </ul>

        <Field error={errors.terms}>
          <Checkbox
            label="I agree to be kind, cite my sources, and follow the CodeHer community guidelines."
            checked={accepted}
            onChange={(event) => setAccepted(event.target.checked)}
          />
        </Field>

        <Button type="submit" block size="lg" loading={busy}>
          <UserPlus size={17} /> Get Started
        </Button>
      </form>
    </AuthShell>
  );
}
