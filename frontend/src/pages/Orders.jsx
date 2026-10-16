import { useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import { Check, ChevronRight, PackageOpen } from "lucide-react";
import { Alert, Breadcrumbs, EmptyState, Pagination, Spinner } from "../components/ui";
import { api } from "../lib/api";
import { formatDate, money, STATUS_LABELS, STATUS_STEPS } from "../lib/format";
import { useDocumentTitle, useFetch } from "../lib/hooks";

export const StatusPill = ({ status }) => <span className={`pill pill-${status}`}>{STATUS_LABELS[status] || status}</span>;

export function Orders() {
  useDocumentTitle("My orders");
  const [page, setPage] = useState(1);
  const { data, meta, loading, error } = useFetch(() => api.get("/orders/", { auth: true, query: { page } }), [page]);
  if (loading && !data) return <Spinner label="Loading orders" />;
  return (
    <div className="container page narrow-page">
      <header className="page-head"><h1>My orders</h1></header>
      {error && <Alert>{error.message}</Alert>}
      {data && data.length === 0 && (
        <EmptyState icon={PackageOpen} title="No orders yet" action={<Link to="/shop" className="btn btn-primary">Start shopping</Link>}>
          When you place an order it will appear here.
        </EmptyState>
      )}
      <ul className="order-list">
        {(data || []).map((o) => (
          <li key={o.uuid}>
            <Link to={`/orders/${o.uuid}`} className="order-card">
              <div>
                <strong>{o.order_number}</strong>
                <p className="muted small">Placed {formatDate(o.created_at)}</p>
              </div>
              <StatusPill status={o.status} />
              <strong className="order-total">{money(o.total)}</strong>
              <ChevronRight size={18} aria-hidden="true" />
            </Link>
          </li>
        ))}
      </ul>
      <Pagination page={page} totalPages={meta?.total_pages} onChange={setPage} />
    </div>
  );
}

function Tracker({ status }) {
  if (!STATUS_STEPS.includes(status)) {
    return <Alert type={status === "refunded" ? "success" : "error"}>This order is <strong>{STATUS_LABELS[status].toLowerCase()}</strong>.</Alert>;
  }
  const current = STATUS_STEPS.indexOf(status);
  return (
    <ol className="tracker" aria-label="Order progress">
      {STATUS_STEPS.map((s, i) => (
        <li key={s} className={i < current ? "done" : i === current ? "current" : ""} aria-current={i === current ? "step" : undefined}>
          <span className="dot">{i < current ? <Check size={14} /> : i + 1}</span>
          <span className="tlabel">{STATUS_LABELS[s]}</span>
        </li>
      ))}
    </ol>
  );
}

export function OrderDetail() {
  const { uuid } = useParams();
  const location = useLocation();
  const { data: o, loading, error } = useFetch(() => api.get(`/orders/${uuid}/`, { auth: true }), [uuid]);
  useDocumentTitle(o ? `Order ${o.order_number}` : "Order");
  if (loading && !o) return <Spinner label="Loading order" />;
  if (error || !o) {
    return (
      <div className="container page">
        <EmptyState title="Order not found" action={<Link to="/orders" className="btn btn-primary">Back to orders</Link>}>
          We couldn’t find that order on your account.
        </EmptyState>
      </div>
    );
  }
  return (
    <div className="container page narrow-page">
      <Breadcrumbs items={[{ label: "My orders", to: "/orders" }, { label: o.order_number }]} />
      {location.state?.placed && <Alert type="success"><strong>Thank you — your order is placed!</strong> We’ll confirm it shortly. You’ll pay {money(o.total)} on delivery.</Alert>}
      <header className="page-head row">
        <div>
          <h1>{o.order_number}</h1>
          <p className="muted">Placed {formatDate(o.created_at)}</p>
        </div>
        <StatusPill status={o.status} />
      </header>
      <section className="card"><Tracker status={o.status} /></section>
      <div className="order-grid">
        <section className="card">
          <h2>Items</h2>
          <ul className="mini-lines">
            {o.items.map((it) => (
              <li key={`${it.sku}`} className="plain">
                <div>
                  <p>{it.product_name}</p>
                  <p className="muted small">{it.variant_label} × {it.quantity} · {money(it.unit_price)} each</p>
                </div>
                <span>{money(it.subtotal)}</span>
              </li>
            ))}
          </ul>
          <div className="sum-row"><span>Subtotal</span><span>{money(o.subtotal)}</span></div>
          <div className="sum-row"><span>Delivery</span><span>{money(o.delivery_charge)}</span></div>
          <div className="sum-row total"><span>Total</span><strong>{money(o.total)}</strong></div>
        </section>
        <section className="card">
          <h2>Delivery</h2>
          <address>
            <strong>{o.shipping_full_name}</strong><br />
            {o.shipping_address_line}<br />
            {o.shipping_city} {o.shipping_postal_code}<br />
            {o.shipping_phone}
          </address>
          <h2 className="mt">Payment</h2>
          <p>Cash on delivery · <span className="muted">{o.payment_status === "paid" ? "Paid" : "Pay on arrival"}</span></p>
          {o.notes && (<><h2 className="mt">Notes</h2><p>{o.notes}</p></>)}
        </section>
      </div>
    </div>
  );
}
