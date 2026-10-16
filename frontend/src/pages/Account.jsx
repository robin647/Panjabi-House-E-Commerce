import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { MapPin, Pencil, Plus, Trash2 } from "lucide-react";
import AddressForm from "../components/AddressForm";
import { Alert, EmptyState, Field, Modal, Spinner } from "../components/ui";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { api } from "../lib/api";
import { errorText, fieldErrors } from "../lib/format";
import { useDocumentTitle, useFetch } from "../lib/hooks";

function ProfileTab() {
  const { user, setUser } = useAuth();
  const { push } = useToast();
  const [first, setFirst] = useState(user.first_name || "");
  const [last, setLast] = useState(user.last_name || "");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function save(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const { data } = await api.patch("/profile/", { first_name: first, last_name: last }, { auth: true });
      setUser(data);
      push("Profile updated.");
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(false);
    }
  }
  return (
    <form className="card form-grid" onSubmit={save}>
      <h2 className="span-2">Your details</h2>
      <Alert>{error}</Alert>
      <Field label="First name" value={first} onChange={(e) => setFirst(e.target.value)} autoComplete="given-name" />
      <Field label="Last name" value={last} onChange={(e) => setLast(e.target.value)} autoComplete="family-name" />
      <Field label="Email" value={user.email || "—"} readOnly hint="Your sign-in email can’t be changed here." />
      <Field label="Phone" value={user.phone_number || "—"} readOnly />
      <div className="form-actions span-2"><button type="submit" className="btn btn-primary" disabled={busy}>{busy ? "Saving…" : "Save changes"}</button></div>
    </form>
  );
}

function AddressesTab() {
  const { push } = useToast();
  const { data, loading, reload } = useFetch(() => api.get("/addresses/", { auth: true }), []);
  const [editing, setEditing] = useState(null); // null | {} (new) | address
  async function act(fn, ok) {
    try {
      await fn();
      await reload();
      if (ok) push(ok);
    } catch (err) {
      push(errorText(err), "error");
    }
  }
  async function save(values) {
    if (editing.uuid) await api.patch(`/addresses/${editing.uuid}/`, values, { auth: true });
    else await api.post("/addresses/", values, { auth: true });
    setEditing(null);
    await reload();
    push("Address saved.");
  }
  if (loading && !data) return <Spinner label="Loading addresses" />;
  return (
    <div>
      <div className="section-head">
        <h2>Saved addresses</h2>
        <button type="button" className="btn btn-primary btn-sm" onClick={() => setEditing({})}><Plus size={16} /> Add address</button>
      </div>
      {data?.length === 0 && <EmptyState icon={MapPin} title="No saved addresses">Add one now to speed up checkout.</EmptyState>}
      <div className="addr-cards">
        {(data || []).map((a) => (
          <article key={a.uuid} className="card addr-card">
            <header>
              <strong>{a.full_name}</strong>
              {a.is_default && <em className="tag">Default</em>}
            </header>
            <p>{a.address_line}<br />{a.city} {a.postal_code}<br /><span className="muted">{a.phone}</span></p>
            {a.delivery_instructions && <p className="muted small">“{a.delivery_instructions}”</p>}
            <footer>
              <button type="button" className="link-btn" onClick={() => setEditing(a)}><Pencil size={14} /> Edit</button>
              {!a.is_default && <button type="button" className="link-btn" onClick={() => act(() => api.post(`/addresses/${a.uuid}/set-default/`, {}, { auth: true }), "Default address updated.")}>Make default</button>}
              <button type="button" className="link-btn danger" aria-label={`Delete address for ${a.full_name}`} onClick={() => window.confirm("Delete this address?") && act(() => api.delete(`/addresses/${a.uuid}/`, { auth: true }), "Address deleted.")}><Trash2 size={14} /> Delete</button>
            </footer>
          </article>
        ))}
      </div>
      {editing && (
        <Modal title={editing.uuid ? "Edit address" : "New address"} onClose={() => setEditing(null)}>
          <AddressForm initial={editing.uuid ? editing : null} onSubmit={save} onCancel={() => setEditing(null)} />
        </Modal>
      )}
    </div>
  );
}

function SecurityTab() {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const [oldPassword, setOld] = useState("");
  const [newPassword, setNew] = useState("");
  const [errors, setErrors] = useState({});
  const [general, setGeneral] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setErrors({});
    setGeneral("");
    try {
      await api.post("/auth/change-password/", { old_password: oldPassword, new_password: newPassword }, { auth: true });
      await logout(); // the server revokes every session on password change
      navigate("/login", { replace: true, state: { notice: "Password changed. Please sign in again." } });
    } catch (err) {
      const fe = fieldErrors(err);
      setErrors(fe);
      if (!Object.keys(fe).length) setGeneral(errorText(err));
    } finally {
      setBusy(false);
    }
  }
  return (
    <form className="card stack narrow-form" onSubmit={submit}>
      <h2>Change password</h2>
      <p className="muted small">For your security you’ll be signed out everywhere after changing it.</p>
      <Alert>{general}</Alert>
      <Field label="Current password" type="password" value={oldPassword} onChange={(e) => setOld(e.target.value)} error={errors.old_password} autoComplete="current-password" required />
      <Field label="New password" type="password" value={newPassword} onChange={(e) => setNew(e.target.value)} error={errors.new_password} autoComplete="new-password" required />
      <button type="submit" className="btn btn-primary" disabled={busy}>{busy ? "Updating…" : "Change password"}</button>
    </form>
  );
}

const TABS = [["profile", "Profile"], ["addresses", "Addresses"], ["security", "Security"]];

export default function Account() {
  useDocumentTitle("My account");
  const [sp, setSp] = useSearchParams();
  const tab = TABS.some(([k]) => k === sp.get("tab")) ? sp.get("tab") : "profile";
  return (
    <div className="container page narrow-page">
      <header className="page-head"><h1>My account</h1></header>
      <div className="tabs" role="tablist" aria-label="Account sections">
        {TABS.map(([k, label]) => (
          <button key={k} type="button" role="tab" aria-selected={tab === k} className={tab === k ? "is-on" : ""} onClick={() => setSp({ tab: k })}>{label}</button>
        ))}
      </div>
      {tab === "profile" && <ProfileTab />}
      {tab === "addresses" && <AddressesTab />}
      {tab === "security" && <SecurityTab />}
    </div>
  );
}
