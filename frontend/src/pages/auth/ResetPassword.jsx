import { useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ShieldCheck } from "lucide-react";
import AuthShell from "./AuthShell";
import { Alert, Button, Field, Input, PasswordInput } from "../../components/ui";
import { api, endpoints } from "../../services/api";
import "./auth.css";

export default function ResetPassword() {
  const [params] = useSearchParams();
  const [form, setForm] = useState({
    uid: params.get("uid") ?? "",
    token: params.get("token") ?? "",
    new_password: "",
    new_password2: "",
  });
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState("");
  const [done, setDone] = useState(false);
  const [busy, setBusy] = useState(false);

  const fromLink = useMemo(() => Boolean(params.get("uid") && params.get("token")), [params]);
  const set = (key) => (event) => setForm((current) => ({ ...current, [key]: event.target.value }));

  const submit = async (event) => {
    event.preventDefault();
    setFormError("");
    const next = {};
    if (!form.uid.trim()) next.uid = "Reset codes start with your account id.";
    if (!form.token.trim()) next.token = "Paste the token from the reset link.";
    if (form.new_password.length < 8) next.new_password = "Use at least 8 characters.";
    if (form.new_password !== form.new_password2) next.new_password2 = "Passwords do not match.";
    setErrors(next);
    if (Object.keys(next).length) return;

    setBusy(true);
    try {
      await api.post(endpoints.resetPassword, form);
      setDone(true);
    } catch (error) {
      setErrors(error.fieldErrors ?? {});
      setFormError(error.detail || "This reset link is invalid or has expired.");
    } finally {
      setBusy(false);
    }
  };

  if (done) {
    return (
      <AuthShell
        title="Password updated"
        subtitle="Your new password is active. Any other devices were signed out."
        footer={
          <>
            <Button to="/signin" block>
              Sign in with your new password
            </Button>
          </>
        }
      >
        <Alert variant="success" title="All set">
          <ShieldCheck size={16} style={{ display: "inline", verticalAlign: "-3px", marginRight: 6 }} />
          Keep it somewhere safe — CodeHer staff cannot read your password, only reset it.
        </Alert>
      </AuthShell>
    );
  }

  return (
    <AuthShell
      title="Choose a new password"
      subtitle={fromLink ? "This link was opened from your reset email." : "Paste the uid and token from your reset link."}
      footer={
        <>
          Link expired? <Link to="/forgot-password">Request a new one</Link>
        </>
      }
    >
      <form className="stack" style={{ gap: "var(--sp-4)" }} onSubmit={submit} noValidate>
        {formError && <Alert variant="error">{formError}</Alert>}

        {!fromLink && (
          <div className="form-grid form-grid--2">
            <Field label="Account id" error={errors.uid} htmlFor="rp-uid" required>
              <Input id="rp-uid" value={form.uid} onChange={set("uid")} placeholder="1" error={errors.uid} />
            </Field>
            <Field label="Token" error={errors.token} htmlFor="rp-token" required>
              <Input id="rp-token" value={form.token} onChange={set("token")} placeholder="abc123…" error={errors.token} />
            </Field>
          </div>
        )}

        <Field label="New password" error={errors.new_password} htmlFor="rp-password" required>
          <PasswordInput id="rp-password" value={form.new_password} onChange={set("new_password")} autoComplete="new-password" error={errors.new_password} required />
        </Field>
        <Field label="Confirm new password" error={errors.new_password2} htmlFor="rp-password2" required>
          <PasswordInput id="rp-password2" value={form.new_password2} onChange={set("new_password2")} autoComplete="new-password" error={errors.new_password2} required />
        </Field>

        <Button type="submit" block size="lg" loading={busy}>
          Update password
        </Button>
      </form>
    </AuthShell>
  );
}
