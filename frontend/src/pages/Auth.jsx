import { useState } from "react";
import { Link, Navigate, useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { Logo } from "../components/Header";
import ProductImage from "../components/ProductImage";
import { Alert, Field } from "../components/ui";
import { useAuth } from "../context/AuthContext";
import { api } from "../lib/api";
import { errorText, fieldErrors, SHOP_NAME } from "../lib/format";
import { useDocumentTitle } from "../lib/hooks";

function AuthShell({ title, subtitle, children, footer }) {
  return (
    <div className="auth">
      <aside className="auth-side" aria-hidden="true">
        <ProductImage name="" seed="auth-art" />
        <div className="auth-side-copy">
          <Logo light />
          <h2>Dressed for every occasion.</h2>
          <p>Sign in to track orders, save addresses and check out faster.</p>
        </div>
      </aside>
      <div className="auth-main">
        <div className="auth-card">
          <h1>{title}</h1>
          {subtitle && <p className="muted">{subtitle}</p>}
          {children}
          {footer && <p className="auth-foot">{footer}</p>}
        </div>
      </div>
    </div>
  );
}

function useSubmit(fn) {
  const [busy, setBusy] = useState(false);
  const [errors, setErrors] = useState({});
  const [general, setGeneral] = useState("");
  async function run(e) {
    e.preventDefault();
    setBusy(true);
    setErrors({});
    setGeneral("");
    try {
      await fn();
    } catch (err) {
      const fe = fieldErrors(err);
      setErrors(fe);
      if (!Object.keys(fe).length || err.status === 401 || err.status === 429) setGeneral(errorText(err));
    } finally {
      setBusy(false);
    }
  }
  return { busy, errors, general, run, setGeneral };
}

export function Login() {
  useDocumentTitle("Sign in");
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = location.state?.from || "/";
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const form = useSubmit(async () => {
    await login(identifier.trim(), password);
    navigate(from, { replace: true });
  });
  if (user) return <Navigate to={from} replace />;
  return (
    <AuthShell title="Welcome back" subtitle="Sign in with your email or phone number." footer={<>New here? <Link to="/register" state={location.state}>Create an account</Link></>}>
      {location.state?.notice && <Alert type="success">{location.state.notice}</Alert>}
      <form onSubmit={form.run} noValidate className="stack">
        <Alert>{form.general}</Alert>
        <Field label="Email or phone" value={identifier} onChange={(e) => setIdentifier(e.target.value)} error={form.errors.identifier} autoComplete="username" required />
        <Field label="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} error={form.errors.password} autoComplete="current-password" required />
        <Link to="/forgot-password" className="small">Forgot your password?</Link>
        <button type="submit" className="btn btn-primary btn-block btn-lg" disabled={form.busy}>{form.busy ? "Signing in…" : "Sign in"}</button>
      </form>
    </AuthShell>
  );
}

export function Register() {
  useDocumentTitle("Create account");
  const { user, register } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = location.state?.from || "/";
  const [v, setV] = useState({ first_name: "", last_name: "", email: "", phone_number: "", password: "", password_confirm: "" });
  const set = (k) => (e) => setV((s) => ({ ...s, [k]: e.target.value }));
  const [clientError, setClientError] = useState("");
  const form = useSubmit(async () => {
    setClientError("");
    if (!v.email.trim() && !v.phone_number.trim()) {
      setClientError("Enter an email address or a phone number.");
      return;
    }
    const payload = Object.fromEntries(Object.entries(v).filter(([, val]) => val.trim() !== ""));
    await register(payload);
    navigate(from, { replace: true });
  });
  if (user) return <Navigate to={from} replace />;
  return (
    <AuthShell title="Create your account" subtitle={`Join ${SHOP_NAME} — it takes a minute.`} footer={<>Already registered? <Link to="/login" state={location.state}>Sign in</Link></>}>
      <form onSubmit={form.run} noValidate className="form-grid">
        <Alert>{form.general || clientError}</Alert>
        <Field label="First name" value={v.first_name} onChange={set("first_name")} error={form.errors.first_name} autoComplete="given-name" />
        <Field label="Last name" value={v.last_name} onChange={set("last_name")} error={form.errors.last_name} autoComplete="family-name" />
        <Field className="span-2" label="Email" type="email" value={v.email} onChange={set("email")} error={form.errors.email} autoComplete="email" />
        <Field className="span-2" label="Phone" type="tel" value={v.phone_number} onChange={set("phone_number")} error={form.errors.phone_number} hint="Email or phone — at least one is required." placeholder="01XXXXXXXXX" autoComplete="tel" />
        <Field className="span-2" label="Password" type="password" value={v.password} onChange={set("password")} error={form.errors.password} hint="At least 8 characters; avoid common passwords." autoComplete="new-password" required />
        <Field className="span-2" label="Confirm password" type="password" value={v.password_confirm} onChange={set("password_confirm")} error={form.errors.password_confirm} autoComplete="new-password" required />
        <button type="submit" className="btn btn-primary btn-block btn-lg span-2" disabled={form.busy}>{form.busy ? "Creating account…" : "Create account"}</button>
      </form>
    </AuthShell>
  );
}

export function ForgotPassword() {
  useDocumentTitle("Forgot password");
  const [identifier, setIdentifier] = useState("");
  const [sent, setSent] = useState("");
  const form = useSubmit(async () => {
    const { message } = await api.post("/auth/forgot-password/", { identifier: identifier.trim() });
    setSent(message);
  });
  return (
    <AuthShell title="Reset your password" subtitle="Enter your email or phone and we’ll send a reset link." footer={<Link to="/login">Back to sign in</Link>}>
      {sent ? (
        <Alert type="success">{sent} Check your inbox (and spam folder).</Alert>
      ) : (
        <form onSubmit={form.run} noValidate className="stack">
          <Alert>{form.general}</Alert>
          <Field label="Email or phone" value={identifier} onChange={(e) => setIdentifier(e.target.value)} error={form.errors.identifier} required />
          <button type="submit" className="btn btn-primary btn-block btn-lg" disabled={form.busy}>{form.busy ? "Sending…" : "Send reset link"}</button>
        </form>
      )}
    </AuthShell>
  );
}

export function ResetPassword() {
  useDocumentTitle("Choose a new password");
  const [sp] = useSearchParams();
  const navigate = useNavigate();
  const uid = sp.get("uid");
  const token = sp.get("token");
  const [password, setPassword] = useState("");
  const form = useSubmit(async () => {
    await api.post("/auth/reset-password/", { uid, token, new_password: password });
    navigate("/login", { replace: true, state: { notice: "Password updated. You can sign in with your new password." } });
  });
  return (
    <AuthShell title="Choose a new password" footer={<Link to="/login">Back to sign in</Link>}>
      {!uid || !token ? (
        <Alert>This reset link is incomplete. Please request a new one.</Alert>
      ) : (
        <form onSubmit={form.run} noValidate className="stack">
          <Alert>{form.general || form.errors.token}</Alert>
          <Field label="New password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} error={form.errors.new_password} autoComplete="new-password" required />
          <button type="submit" className="btn btn-primary btn-block btn-lg" disabled={form.busy}>{form.busy ? "Saving…" : "Update password"}</button>
        </form>
      )}
    </AuthShell>
  );
}
