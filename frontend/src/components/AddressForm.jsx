import { useState } from "react";
import { CITY_SUGGESTIONS, fieldErrors, isDhaka } from "../lib/format";
import { Alert, Field } from "./ui";

const EMPTY = {
  full_name: "", phone: "", address_line: "", city: "Dhaka", postal_code: "", delivery_instructions: "", is_default: false,
};

export default function AddressForm({ initial, onSubmit, onCancel, submitLabel = "Save address" }) {
  const [values, setValues] = useState({ ...EMPTY, ...(initial || {}) });
  const [errors, setErrors] = useState({});
  const [general, setGeneral] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setValues((v) => ({ ...v, [k]: e.target.type === "checkbox" ? e.target.checked : e.target.value }));

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setErrors({});
    setGeneral("");
    try {
      await onSubmit(values);
    } catch (err) {
      const fe = fieldErrors(err);
      setErrors(fe);
      if (!Object.keys(fe).length) setGeneral(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="form-grid" onSubmit={submit} noValidate>
      <Alert>{general}</Alert>
      <Field label="Full name" value={values.full_name} onChange={set("full_name")} error={errors.full_name} autoComplete="name" required />
      <Field label="Phone" type="tel" value={values.phone} onChange={set("phone")} error={errors.phone} autoComplete="tel" placeholder="01XXXXXXXXX" required />
      <Field className="span-2" label="Address" value={values.address_line} onChange={set("address_line")} error={errors.address_line} autoComplete="street-address" placeholder="House, road, area" required />
      <Field
        label="City"
        list="city-options"
        value={values.city}
        onChange={set("city")}
        error={errors.city}
        hint={isDhaka(values.city) ? "Inside Dhaka delivery rate applies." : "Outside Dhaka delivery rate applies."}
        autoComplete="address-level2"
        required
      />
      <datalist id="city-options">
        {CITY_SUGGESTIONS.map((c) => (
          <option key={c} value={c} />
        ))}
      </datalist>
      <Field label="Postal code" value={values.postal_code} onChange={set("postal_code")} error={errors.postal_code} autoComplete="postal-code" />
      <Field className="span-2" label="Delivery instructions (optional)" value={values.delivery_instructions} onChange={set("delivery_instructions")} error={errors.delivery_instructions} placeholder="e.g. call before arriving" />
      <label className="check span-2">
        <input type="checkbox" checked={values.is_default} onChange={set("is_default")} /> Make this my default address
      </label>
      <div className="form-actions span-2">
        {onCancel && (
          <button type="button" className="btn btn-ghost" onClick={onCancel}>
            Cancel
          </button>
        )}
        <button type="submit" className="btn btn-primary" disabled={busy}>
          {busy ? "Saving…" : submitLabel}
        </button>
      </div>
    </form>
  );
}
