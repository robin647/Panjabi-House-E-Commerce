import { Link, useNavigate } from "react-router-dom";
import { ShoppingBag, X } from "lucide-react";
import { useCart } from "../context/CartContext";
import { money } from "../lib/format";
import { useEscape, useLockBody } from "../lib/hooks";
import CartLines from "./CartLines";
import { EmptyState } from "./ui";

export default function CartDrawer() {
  const { cart, drawerOpen, closeDrawer } = useCart();
  const navigate = useNavigate();
  useLockBody(drawerOpen);
  useEscape(closeDrawer, drawerOpen);

  return (
    <div className={`drawer-root ${drawerOpen ? "is-open" : ""}`} aria-hidden={!drawerOpen}>
      <div className="drawer-backdrop" onClick={closeDrawer} />
      <aside className="drawer" role="dialog" aria-modal="true" aria-label="Shopping cart">
        <header>
          <h2>Your cart {cart.item_count > 0 && <span className="muted">({cart.item_count})</span>}</h2>
          <button type="button" className="icon-btn" aria-label="Close cart" onClick={closeDrawer}>
            <X size={20} />
          </button>
        </header>
        <div className="drawer-body">
          {cart.items.length === 0 ? (
            <EmptyState
              icon={ShoppingBag}
              title="Your cart is empty"
              action={
                <Link to="/shop" className="btn btn-primary" onClick={closeDrawer}>
                  Start shopping
                </Link>
              }
            />
          ) : (
            <CartLines onNavigate={closeDrawer} />
          )}
        </div>
        {cart.items.length > 0 && (
          <footer>
            <div className="sum-row">
              <span>Subtotal</span>
              <strong>{money(cart.subtotal)}</strong>
            </div>
            <p className="muted small">Delivery charge is added at checkout.</p>
            <button
              type="button"
              className="btn btn-primary btn-block"
              onClick={() => {
                closeDrawer();
                navigate("/checkout");
              }}
            >
              Checkout
            </button>
            <Link to="/cart" className="btn btn-ghost btn-block" onClick={closeDrawer}>
              View cart
            </Link>
          </footer>
        )}
      </aside>
    </div>
  );
}
