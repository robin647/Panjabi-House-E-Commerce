import { Link } from "react-router-dom";
import { LogIn, ShoppingBag } from "lucide-react";
import CartLines from "../components/CartLines";
import { EmptyState } from "../components/ui";
import { useAuth } from "../context/AuthContext";
import { useCart } from "../context/CartContext";
import { money } from "../lib/format";
import { useDocumentTitle, useShopConfig } from "../lib/hooks";

export default function Cart() {
  useDocumentTitle("Your cart");
  const { user } = useAuth();
  const { cart } = useCart();
  const config = useShopConfig();

  if (!user) {
    return (
      <div className="container page">
        <EmptyState icon={LogIn} title="Sign in to see your cart" action={<Link to="/login" state={{ from: "/cart" }} className="btn btn-primary">Sign in</Link>}>
          Your cart is saved to your account, so you can pick up on any device.
        </EmptyState>
      </div>
    );
  }
  if (cart.items.length === 0) {
    return (
      <div className="container page">
        <EmptyState icon={ShoppingBag} title="Your cart is empty" action={<Link to="/shop" className="btn btn-primary">Browse the shop</Link>}>
          Add something you love and it will show up here.
        </EmptyState>
      </div>
    );
  }
  return (
    <div className="container page">
      <header className="page-head"><h1>Your cart</h1></header>
      <div className="cart-layout">
        <div className="card"><CartLines /></div>
        <aside className="card summary">
          <h2>Order summary</h2>
          <div className="sum-row"><span>Subtotal ({cart.item_count} items)</span><strong>{money(cart.subtotal)}</strong></div>
          <div className="sum-row muted"><span>Delivery</span><span>{money(config.delivery_charge_inside_dhaka)} – {money(config.delivery_charge_outside_dhaka)}</span></div>
          <p className="muted small">Exact delivery charge depends on your address and is shown at checkout.</p>
          <Link to="/checkout" className="btn btn-primary btn-block btn-lg">Proceed to checkout</Link>
          <Link to="/shop" className="btn btn-ghost btn-block">Continue shopping</Link>
        </aside>
      </div>
    </div>
  );
}
