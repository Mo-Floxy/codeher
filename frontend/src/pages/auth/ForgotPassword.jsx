import { useState } from "react";
import { Link } from "react-router-dom";
import { KeyRound, MailCheck } from "lucide-react";
import AuthShell from "./AuthShell";
import { Alert, Button, Field, Input } from "../../components/ui";
import { api, endpoints } from "../../services/api";
import "./auth.css";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [fieldError, setFieldError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (event) => {
    event.preventDefault();
    setError("");
    setFieldError("");
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)) {
      setFieldError("Enter the email address on your account.");
      return;
    }
    setBusy(true);
    try {
      const data = await api.post(endpoints.forgotPassword, { email });
      setResult(data);
    } catch (err) {
      setError(err.detail || "We could not start a reset. Try again in a moment.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthShell
      title="Reset your password"
      subtitle="We will send a link to the email address on your account."
      footer={
        <>
          Remembered it? <Link to="/signin">Back to sign in</Link>
        </>
      }
    >
      {result ? (
        <div className="stack">
          <Alert variant="success" title="Request received">
            If <strong>{result.email ?? email}</strong> matches an account, a reset link is on its way.
            The link expires in {result.expires_in_hours ?? 24} hours.
          </Alert>
          {result.reset_url && (
            <Alert variant="info" title="Email delivery is not configured">
              <div className="stack" style={{ gap: 8 }}>
                <span>
                  Django is running with DEBUG enabled and no SMTP credentials, so the reset link is
                  returned directly instead of emailed.
                </span>
                <Link to={`/reset-password?uid=${result.uid}&token=${result.token}`}>
                  <Button size="sm" variant="outline">
                    <KeyRound size={14} /> Open the reset form
                  </Button>
                </Link>
              </div>
            </Alert>
          )}
          <Button variant="ghost" to="/signin" block>
            Back to sign in
          </Button>
        </div>
      ) : (
        <form className="stack" style={{ gap: "var(--sp-4)" }} onSubmit={submit} noValidate>
          {error && <Alert variant="error">{error}</Alert>}
          <Field label="Email address" error={fieldError} htmlFor="fp-email" required>
            <Input
              id="fp-email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@example.com"
              autoComplete="email"
              error={fieldError}
              required
            />
          </Field>
          <Button type="submit" block size="lg" loading={busy}>
            <MailCheck size={17} /> Send reset link
          </Button>
        </form>
      )}
    </AuthShell>
  );
}
