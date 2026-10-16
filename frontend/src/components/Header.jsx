import { useEffect, useRef, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { ChevronDown, LogOut, Menu, Package, Search, ShoppingBag, User, UserCog, X } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { useCart } from "../context/CartContext";
import { money, SHOP_NAME } from "../lib/format";
import { useCategories, useClickOutside, useShopConfig } from "../lib/hooks";

export function Logo({ light = false }) {
  return (
    <Link to="/" className={`brand ${light ? "brand-light" : ""}`} aria-label={`${SHOP_NAME} home`}>
      <svg viewBox="0 0 64 64" width="34" height="34" aria-hidden="true">
        <rect width="64" height="64" rx="14" fill={light ? "rgba(255,255,255,.14)" : "#7a1f2b"} />
        <path d="M22 14l10 6 10-6 14 14-6 10-8-4v24H22V34l-8 4-6-10z" fill="none" stroke="#f5ecd9" strokeWidth="3" strokeLinejoin="round" />
        <circle cx="32" cy="30" r="1.8" fill="#e0b25c" />
        <circle cx="32" cy="38" r="1.8" fill="#e0b25c" />
      </svg>
      <span>{SHOP_NAME}</span>
    </Link>
  );
}

export default function Header() {
  const { user, logout } = useAuth();
  const { cart, openDrawer } = useCart();
  const categories = useCategories();
  const config = useShopConfig();
  const navigate = useNavigate();
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [catOpen, setCatOpen] = useState(false);
  const [acctOpen, setAcctOpen] = useState(false);
  const [q, setQ] = useState("");
  const catRef = useRef(null);
  const acctRef = useRef(null);
  useClickOutside(catRef, () => setCatOpen(false), catOpen);
  useClickOutside(acctRef, () => setAcctOpen(false), acctOpen);

  useEffect(() => {
    setMenuOpen(false);
    setSearchOpen(false);
    setCatOpen(false);
    setAcctOpen(false);
  }, [location.pathname, location.search]);

  const search = new URLSearchParams(location.search);
  const onShop = location.pathname === "/shop";
  const active = {
    shop: onShop && !search.get("new_collection") && !search.get("on_sale"),
    new: onShop && search.get("new_collection") === "true",
    sale: onShop && search.get("on_sale") === "true",
  };

  function submitSearch(e) {
    e.preventDefault();
    const term = q.trim();
    navigate(term ? `/shop?search=${encodeURIComponent(term)}` : "/shop");
  }

  async function signOut() {
    await logout();
    navigate("/");
  }

  const searchForm = (id) => (
    <form className="search" role="search" onSubmit={submitSearch}>
      <Search size={18} aria-hidden="true" />
      <input id={id} type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search panjabi, koti, blazer…" aria-label="Search products" />
    </form>
  );

  return (
    <>
      <div className="announce">
        Cash on delivery on every order · Inside Dhaka {money(config.delivery_charge_inside_dhaka)} · Outside Dhaka {money(config.delivery_charge_outside_dhaka)}
      </div>
      <header className="site-header">
        <div className="container header-row">
          <button type="button" className="icon-btn menu-btn" aria-label={menuOpen ? "Close menu" : "Open menu"} aria-expanded={menuOpen} onClick={() => setMenuOpen((o) => !o)}>
            {menuOpen ? <X size={22} /> : <Menu size={22} />}
          </button>
          <Logo />

          <nav className="nav-main" aria-label="Main">
            <Link to="/shop" className={active.shop ? "is-active" : ""}>Shop</Link>
            <Link to="/shop?new_collection=true" className={active.new ? "is-active" : ""}>New in</Link>
            <Link to="/shop?on_sale=true" className={active.sale ? "is-active" : ""}>Sale</Link>
            {categories.length > 0 && (
              <div className="menu-wrap" ref={catRef}>
                <button type="button" className="nav-btn" aria-expanded={catOpen} aria-haspopup="true" onClick={() => setCatOpen((o) => !o)}>
                  Categories <ChevronDown size={16} />
                </button>
                {catOpen && (
                  <div className="menu-panel">
                    {categories.map((c) => (
                      <Link key={c.uuid} to={`/shop?category=${c.slug}`}>{c.name}</Link>
                    ))}
                  </div>
                )}
              </div>
            )}
          </nav>

          <div className="header-search">{searchForm("search-desktop")}</div>

          <div className="header-actions">
            <button type="button" className="icon-btn search-toggle" aria-label="Search" aria-expanded={searchOpen} onClick={() => setSearchOpen((o) => !o)}>
              <Search size={21} />
            </button>
            {user ? (
              <div className="menu-wrap" ref={acctRef}>
                <button type="button" className="icon-btn" aria-label="Account menu" aria-expanded={acctOpen} aria-haspopup="true" onClick={() => setAcctOpen((o) => !o)}>
                  <User size={21} />
                </button>
                {acctOpen && (
                  <div className="menu-panel menu-right">
                    <p className="menu-hello">Hi, {user.first_name || "there"}</p>
                    <Link to="/account"><UserCog size={16} /> My account</Link>
                    <Link to="/orders"><Package size={16} /> My orders</Link>
                    <button type="button" onClick={signOut}><LogOut size={16} /> Sign out</button>
                  </div>
                )}
              </div>
            ) : (
              <Link to="/login" className="icon-btn" aria-label="Sign in"><User size={21} /></Link>
            )}
            <button type="button" className="icon-btn cart-btn" aria-label={`Open cart, ${cart.item_count} items`} onClick={openDrawer}>
              <ShoppingBag size={21} />
              {cart.item_count > 0 && <span className="cart-count">{cart.item_count}</span>}
            </button>
          </div>
        </div>

        {searchOpen && <div className="container mobile-search">{searchForm("search-mobile")}</div>}

        {menuOpen && (
          <nav className="mobile-menu" aria-label="Mobile">
            <Link to="/shop">Shop all</Link>
            <Link to="/shop?new_collection=true">New in</Link>
            <Link to="/shop?on_sale=true">Sale</Link>
            {categories.length > 0 && <p className="mobile-menu-title">Categories</p>}
            {categories.map((c) => (
              <Link key={c.uuid} to={`/shop?category=${c.slug}`} className="sub">{c.name}</Link>
            ))}
            <p className="mobile-menu-title">Account</p>
            {user ? (
              <>
                <Link to="/account" className="sub">My account</Link>
                <Link to="/orders" className="sub">My orders</Link>
                <button type="button" className="sub" onClick={signOut}>Sign out</button>
              </>
            ) : (
              <>
                <Link to="/login" className="sub">Sign in</Link>
                <Link to="/register" className="sub">Create account</Link>
              </>
            )}
          </nav>
        )}
      </header>
    </>
  );
}
