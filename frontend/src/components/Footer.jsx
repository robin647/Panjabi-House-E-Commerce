import { Link } from "react-router-dom";
import { SHOP_NAME } from "../lib/format";
import { useCategories } from "../lib/hooks";
import { Logo } from "./Header";

export default function Footer() {
  const categories = useCategories();
  return (
    <footer className="site-footer">
      <div className="container footer-grid">
        <div>
          <Logo light />
          <p className="footer-blurb">Panjabi, sherwani, koti, blazers and shirts — honest prices, live stock, cash on delivery.</p>
        </div>
        <div>
          <h4>Shop</h4>
          <Link to="/shop">All products</Link>
          <Link to="/shop?new_collection=true">New in</Link>
          <Link to="/shop?on_sale=true">Sale</Link>
          {categories.slice(0, 4).map((c) => (
            <Link key={c.uuid} to={`/shop?category=${c.slug}`}>{c.name}</Link>
          ))}
        </div>
        <div>
          <h4>Account</h4>
          <Link to="/account">My account</Link>
          <Link to="/orders">Track orders</Link>
          <Link to="/cart">Cart</Link>
        </div>
        <div>
          <h4>Good to know</h4>
          <p>Pay when your order arrives (Cash on Delivery).</p>
          <p>Delivery inside and outside Dhaka.</p>
        </div>
      </div>
      <div className="container footer-bottom">© {new Date().getFullYear()} {SHOP_NAME}. All rights reserved.</div>
    </footer>
  );
}
