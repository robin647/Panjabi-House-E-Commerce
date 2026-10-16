import { useState } from "react";
import { Link } from "react-router-dom";
import { Trash2 } from "lucide-react";
import { useCart } from "../context/CartContext";
import { useToast } from "../context/ToastContext";
import { errorText, money } from "../lib/format";
import ProductImage from "./ProductImage";
import { Stepper } from "./ui";

export default function CartLines({ onNavigate }) {
  const { cart, setQuantity, remove } = useCart();
  const { push } = useToast();
  const [busyId, setBusyId] = useState(null);

  async function run(id, fn) {
    setBusyId(id);
    try {
      await fn();
    } catch (err) {
      push(errorText(err), "error");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <ul className="lines">
      {cart.items.map((item) => {
        const v = item.variant;
        return (
          <li key={item.uuid} className="line">
            <Link to={`/product/${v.product_slug}`} className="line-thumb" onClick={onNavigate} tabIndex={-1} aria-hidden="true">
              <ProductImage src={v.image} name={v.product_name} seed={v.product_slug} />
            </Link>
            <div className="line-main">
              <Link to={`/product/${v.product_slug}`} className="line-name" onClick={onNavigate}>
                {v.product_name}
              </Link>
              <p className="muted">
                {v.size} / {v.color} · {money(item.unit_price)}
              </p>
              <div className="line-controls">
                <Stepper
                  value={item.quantity}
                  max={Math.max(1, v.stock_quantity)}
                  disabled={busyId === item.uuid}
                  onChange={(q) => run(item.uuid, () => setQuantity(item.uuid, q))}
                />
                <button
                  type="button"
                  className="link-btn danger"
                  aria-label={`Remove ${v.product_name}`}
                  disabled={busyId === item.uuid}
                  onClick={() => run(item.uuid, () => remove(item.uuid))}
                >
                  <Trash2 size={15} /> Remove
                </button>
              </div>
            </div>
            <strong className="line-total">{money(item.line_subtotal)}</strong>
          </li>
        );
      })}
    </ul>
  );
}
