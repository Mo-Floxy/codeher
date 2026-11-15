import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { LogIn, Sparkles } from "lucide-react";
import AuthShell from "./AuthShell";
import { Alert, Button, Checkbox, Field, Input, PasswordInput } from "../../components/ui";
import { useAuth } from "../../context/AuthContext";
import { useToast } from "../../context/ToastContext";
import "./auth.css";

// Mirrors Django's password validators so the form agrees with the server.
export const DEMO_ACCOUNTS = [
  { label: "Learner", email: "ada@codeher.dev", password: "CodeHer!Learn2026" },
  { label: "Mentor", email: "grace@codeher.dev", password: "CodeHer!Mentor2026" },
  { label: "Admin", email: "admin@codeher.dev", password: "CodeHer!Admin2026" },
];

export default function SignIn() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const toast = useToast();
  const [form, setForm] = useState({ email: "", password: "" });
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState("");
  const [busy, setBusy] = useState(false);

  const set = (key) => (event) => setForm((current) => ({ ...current, [key]: event.target.value }));

  const validate = () => {
    const next = {};
    if (!form.email.trim()) next.email = "Enter your email address.";
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(form.email)) next.email = "That email does not look right.";
    if (!form.password) next.password = "Enter your password.";
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const submit = async (event) => {
    event.preventDefault();
    setFormError("");
    if (!validate()) return;
    setBusy(true);
    try {
      const user = await login(form);
      toast.success(`Welcome back, ${user.display_name || user.username}!`);
      navigate("/dashboard", { replace: true });
    } catch (error) {
      setErrors(error.fieldErrors ?? {});
      setFormError(error.detail || "We could not sign you in. Check your email and password.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthShell
      title="Welcome back"
      subtitle="Sign in to continue your streak, resume a lesson or reply to your mentor."
      footer={
        <>
          New to CodeHer? <Link to="/signup">Create a free account</Link>
        </>
      }
    >
      <form className="stack" style={{ gap: "var(--sp-4)" }} onSubmit={submit} noValidate>
        {formError && <Alert variant="error">{formError}</Alert>}

        <Field label="Email address" error={errors.email ?? errors.non_field_errors?.[0]} htmlFor="signin-email">
          <Input
            id="signin-email"
            type="email"
            name="email"
            autoComplete="email"
            value={form.email}
            onChange={set("email")}
            placeholder="you@example.com"
            error={errors.email}
            required
          />
        </Field>

        <Field label="Password" error={errors.password} htmlFor="signin-password">
          <PasswordInput
            id="signin-password"
            name="password"
            autoComplete="current-password"
            value={form.password}
            onChange={set("password")}
            placeholder="••••••••"
            error={errors.password}
            required
          />
        </Field>

        <div className="auth-links">
          <Checkbox label="Keep me signed in" name="remember" defaultChecked />
          <Link to="/forgot-password" style={{ fontSize: "var(--fs-sm)" }}>
            Forgot password?
          </Link>
        </div>

        <Button type="submit" block size="lg" loading={busy}>
          <LogIn size={17} /> Sign In
        </Button>

        {import.meta.env.DEV && (
          <div className="divider-label">or fill a seeded demo account</div>
        )}
        {import.meta.env.DEV && (
          <div className="row" style={{ gap: "var(--sp-2)" }}>
            {DEMO_ACCOUNTS.map((account) => (
              <Button
                key={account.email}
                variant="outline"
                size="sm"
                onClick={() => {
                  setForm({ email: account.email, password: account.password });
                  setErrors({});
                  toast.info(`Filled the ${account.label.toLowerCase()} account — sign in to use it.`);
                }}
              >
                <Sparkles size={14} /> {account.label}
              </Button>
            ))}
          </div>
        )}
      </form>
    </AuthShell>
  );
}
