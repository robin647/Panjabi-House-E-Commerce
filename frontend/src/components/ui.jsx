import { useEffect, useId, useState } from "react";
import { Link } from "react-router-dom";
import { AlertCircle, CheckCircle2, ChevronRight, Eye, EyeOff, Loader2, Minus, Plus, X } from "lucide-react";
import { useEscape, useLockBody } from "../lib/hooks";

export function Spinner({ label = "Loading" }) {
  return (
    <div className="spinner" role="status" aria-label={label}>
      <Loader2 className="spin" size={28} />
    </div>
  );
}

export function Alert({ type = "error", children }) {
  if (!children) return null;
  return (
    <div className={`alert alert-${type}`} role={type === "error" ? "alert" : "status"}>
      {type === "error" ? <AlertCircle size={18} /> : <CheckCircle2 size={18} />}
      <div>{children}</div>
    </div>
  );
}

export function EmptyState({ icon: Icon, title, children, action }) {
  return (
    <div className="empty">
      {Icon && (
        <span className="empty-icon">
          <Icon size={30} />
        </span>
      )}
      <h2>{title}</h2>
      {children && <p>{children}</p>}
      {action}
    </div>
  );
}

export function Field({ label, error, hint, as = "input", children, className = "", ...props }) {
  const id = useId();
  const [shown, setShown] = useState(false);
  const isPassword = props.type === "password";
  const Tag = as;
  const describedBy = error ? `${id}-err` : hint ? `${id}-hint` : undefined;
  return (
    <div className={`field ${error ? "has-error" : ""} ${className}`}>
      <label htmlFor={id}>{label}</label>
      <div className="field-control">
        <Tag
          id={id}
          aria-invalid={error ? "true" : undefined}
          aria-describedby={describedBy}
          {...props}
          type={isPassword && shown ? "text" : props.type}
        >
          {children}
        </Tag>
        {isPassword && (
          <button
            type="button"
            className="icon-btn field-toggle"
            aria-label={shown ? "Hide password" : "Show password"}
            onClick={() => setShown((s) => !s)}
          >
            {shown ? <EyeOff size={18} /> : <Eye size={18} />}
          </button>
        )}
      </div>
      {error ? (
        <p className="field-error" id={`${id}-err`}>
          {error}
        </p>
      ) : (
        hint && (
          <p className="field-hint" id={`${id}-hint`}>
            {hint}
          </p>
        )
      )}
    </div>
  );
}

export function Stepper({ value, onChange, min = 1, max = 99, disabled }) {
  return (
    <div className="stepper" role="group" aria-label="Quantity">
      <button type="button" aria-label="Decrease quantity" disabled={disabled || value <= min} onClick={() => onChange(value - 1)}>
        <Minus size={16} />
      </button>
      <output aria-live="polite">{value}</output>
      <button type="button" aria-label="Increase quantity" disabled={disabled || value >= max} onClick={() => onChange(value + 1)}>
        <Plus size={16} />
      </button>
    </div>
  );
}

export function Pagination({ page, totalPages, onChange }) {
  if (!totalPages || totalPages < 2) return null;
  const set = new Set([1, totalPages, page - 1, page, page + 1]);
  const pages = [...set].filter((p) => p >= 1 && p <= totalPages).sort((a, b) => a - b);
  const items = [];
  pages.forEach((p, i) => {
    if (i && p - pages[i - 1] > 1) items.push(`gap-${p}`);
    items.push(p);
  });
  return (
    <nav className="pagination" aria-label="Pagination">
      <button type="button" disabled={page <= 1} onClick={() => onChange(page - 1)}>
        Previous
      </button>
      {items.map((p) =>
        typeof p === "string" ? (
          <span key={p} aria-hidden="true">
            …
          </span>
        ) : (
          <button
            key={p}
            type="button"
            className={p === page ? "is-current" : ""}
            aria-current={p === page ? "page" : undefined}
            aria-label={`Page ${p}`}
            onClick={() => onChange(p)}
          >
            {p}
          </button>
        ),
      )}
      <button type="button" disabled={page >= totalPages} onClick={() => onChange(page + 1)}>
        Next
      </button>
    </nav>
  );
}

export function Breadcrumbs({ items }) {
  return (
    <nav className="breadcrumbs" aria-label="Breadcrumb">
      {items.map((it, i) => (
        <span key={it.label}>
          {it.to ? <Link to={it.to}>{it.label}</Link> : <span aria-current="page">{it.label}</span>}
          {i < items.length - 1 && <ChevronRight size={14} aria-hidden="true" />}
        </span>
      ))}
    </nav>
  );
}

export function Modal({ title, onClose, children }) {
  useLockBody(true);
  useEscape(onClose);
  useEffect(() => {
    const t = setTimeout(() => document.querySelector(".modal input")?.focus(), 30);
    return () => clearTimeout(t);
  }, []);
  return (
    <div className="overlay" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal" role="dialog" aria-modal="true" aria-label={title}>
        <header>
          <h2>{title}</h2>
          <button type="button" className="icon-btn" aria-label="Close" onClick={onClose}>
            <X size={20} />
          </button>
        </header>
        {children}
      </div>
    </div>
  );
}
