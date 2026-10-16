import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Banknote, Plus, ShoppingBag } from "lucide-react";
import AddressForm from "../components/AddressForm";
import ProductImage from "../components/ProductImage";
import { Alert, EmptyState, Field, Spinner } from "../components/ui";
import { useCart } from "../context/CartContext";
import { api } from "../lib/api";
import { errorText, isDhaka, money } from "../lib/format";
import { useDocumentTitle, useFetch, useShopConfig } from "../lib/hooks";

export default function Checkout() {
  useDocumentTitle("Checkout");
  const navigate = useNavigate();
  const { cart, loading: cartLoading, refresh } = useCart();
  const config = useShopConfig();
  const { data: addresses, loading: addrLoading, reload } = useFetch(() => api.get("/addresses/", { auth: true }), []);
  const [selected, setSelected] = useState(null);
  const [adding, setAdding] = useState(false);
  const [notes, setNotes] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const keyRef = useRef({ key: crypto.randomUUID(), sig: "" });

  useEffect(() => {
    if (!addresses) return;
    if (!addresses.length) setAdding(true);
    setSelected((cur) => (addresses.some((a) => a.uuid === cur) ? cur : (addresses.find((a) => a.is_default) || addresses[0])?.uuid ?? null));
  }, [addresses]);

  if ((cartLoading && !cart.items.length) || (addrLoading && !addresses)) return <Spinner label="Loading checkout" />;
  if (!cart.items.length) {
    return (
      <div className="container page">
        <EmptyState icon={ShoppingBag} title="Your cart is empty" action={<Link to="/shop" className="btn btn-primary">Browse the shop</Link>}>
          Add something to your cart before checking out.
        </EmptyState>
      </div>
    );
  }

  const address = (addresses || []).find((a) => a.uuid === selected);
  const delivery = address ? Number(isDhaka(address.city) ? config.delivery_charge_inside_dhaka : config.delivery_charge_outside_dhaka) : null;
  const total = delivery == null ? null : Number(cart.subtotal) + delivery;

  async function saveAddress(values) {
    const { data } = await api.post("/addresses/", values, { auth: true });
    await reload();
    setSelected(data.uuid);
    setAdding(false);
  }

  async function placeOrder() {
    if (!address) return;
    // A fresh idempotency key whenever the request body changes; the same key is reused on
    // retries of the identical request so a double-click or flaky network can't create two orders.
    const sig = `${address.uuid}|${notes}`;
    if (keyRef.current.sig !== sig) keyRef.current = { key: crypto.randomUUID(), sig };
    setBusy(true);
    setError(null);
    try {
      const { data } = await api.post("/checkout/", { address_id: address.uuid, notes }, { auth: true, headers: { "Idempotency-Key": keyRef.current.key } });
      await refresh();
      navigate(`/orders/${data.uuid}`, { replace: true, state: { placed: true } });
    } catch (err) {
      setError(err);
      refresh().catch(() => {});
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="container page">
      <header className="page-head"><h1>Checkout</h1></header>
      <div className="checkout-layout">
        <div className="checkout-main">
          <section className="card">
            <h2>1. Delivery address</h2>
            {(addresses || []).length > 0 && (
              <div className="addr-list" role="radiogroup" aria-label="Delivery address">
                {addresses.map((a) => (
                  <label key={a.uuid} className={`addr ${selected === a.uuid ? "is-on" : ""}`}>
                    <input type="radio" name="address" checked={selected === a.uuid} onChange={() => { setSelected(a.uuid); setAdding(false); }} />
                    <span>
                      <strong>{a.full_name}</strong> {a.is_default && <em className="tag">Default</em>}
                      <br />{a.address_line}, {a.city} {a.postal_code}
                      <br /><span className="muted">{a.phone}</span>
                    </span>
                  </label>
                ))}
              </div>
            )}
            {adding ? (
              <div className="subform">
                <h3>New address</h3>
                <AddressForm onSubmit={saveAddress} onCancel={(addresses || []).length ? () => setAdding(false) : undefined} submitLabel="Save & use this address" />
              </div>
            ) : (
              <button type="button" className="btn btn-ghost" onClick={() => setAdding(true)}><Plus size={16} /> Add a new address</button>
            )}
          </section>

          <section className="card">
            <h2>2. Payment</h2>
            <label className="addr is-on">
              <input type="radio" name="pay" checked readOnly />
              <span><strong><Banknote size={16} /> Cash on delivery</strong><br /><span className="muted">Pay the courier when your order arrives.</span></span>
            </label>
          </section>

          <section className="card">
            <h2>3. Notes <span className="muted">(optional)</span></h2>
            <Field label="Order notes" value={notes} onChange={(e) => setNotes(e.target.value)} maxLength={500} placeholder="Anything we should know?" />
          </section>
        </div>

        <aside className="card summary sticky">
          <h2>Order summary</h2>
          <ul className="mini-lines">
            {cart.items.map((it) => (
              <li key={it.uuid}>
                <div className="line-thumb sm"><ProductImage src={it.variant.image} name={it.variant.product_name} seed={it.variant.product_slug} /></div>
                <div>
                  <p>{it.variant.product_name}</p>
                  <p className="muted small">{it.variant.size} / {it.variant.color} × {it.quantity}</p>
                </div>
                <span>{money(it.line_subtotal)}</span>
              </li>
            ))}
          </ul>
          <div className="sum-row"><span>Subtotal</span><span>{money(cart.subtotal)}</span></div>
          <div className="sum-row"><span>Delivery</span><span>{delivery == null ? "Choose an address" : money(delivery)}</span></div>
          <div className="sum-row total"><span>Total</span><strong>{total == null ? "—" : money(total)}</strong></div>
          <Alert>{error && errorText(error)}</Alert>
          <button type="button" className="btn btn-primary btn-block btn-lg" disabled={!address || busy} onClick={placeOrder}>
            {busy ? "Placing order…" : "Place order"}
          </button>
          <p className="muted small center">Final prices and stock are confirmed when you place the order.</p>
        </aside>
      </div>
    </div>
  );
}
