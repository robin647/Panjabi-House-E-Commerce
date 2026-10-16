import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Banknote, Check, ShoppingBag, Truck } from "lucide-react";
import ProductImage from "../components/ProductImage";
import { ProductGrid } from "../components/ProductCard";
import { Alert, Breadcrumbs, EmptyState, Spinner, Stepper } from "../components/ui";
import { useAddToCart } from "../context/CartContext";
import { api } from "../lib/api";
import { colorHex, money, sortSizes } from "../lib/format";
import { useDocumentTitle, useFetch, useShopConfig } from "../lib/hooks";

function Related({ product }) {
  const { data } = useFetch(
    () => api.get("/products/", { query: { category: product.category_slug, page_size: 5 } }),
    [product.category_slug],
  );
  const items = (data || []).filter((p) => p.uuid !== product.uuid).slice(0, 4);
  if (!items.length) return null;
  return (
    <section className="section">
      <div className="section-head"><h2>You may also like</h2></div>
      <ProductGrid products={items} />
    </section>
  );
}

export default function ProductDetail() {
  const { slug } = useParams();
  const { data: p, loading, error } = useFetch(() => api.get(`/products/${slug}/`), [slug]);
  const addToCart = useAddToCart();
  const config = useShopConfig();
  const [sel, setSel] = useState({ size: null, color: null });
  const [qty, setQty] = useState(1);
  const [busy, setBusy] = useState(false);
  const [added, setAdded] = useState(false);
  useDocumentTitle(p?.name);

  useEffect(() => {
    setSel({ size: null, color: null });
    setQty(1);
    setAdded(false);
  }, [p?.uuid]);

  if (loading && !p) return <Spinner label="Loading product" />;
  if (error || !p) {
    return (
      <div className="container page">
        <EmptyState title={error?.status === 404 ? "We couldn't find that product" : "Something went wrong"} action={<Link to="/shop" className="btn btn-primary">Back to shop</Link>}>
          {error?.status === 404 ? "It may have been removed or is no longer available." : error?.message}
        </EmptyState>
      </div>
    );
  }

  const variants = p.variants;
  // Default to the first purchasable variant on the very first render (no flash of "Unavailable").
  const first = variants.find((v) => v.available) || variants[0];
  const selSize = sel.size ?? first?.size ?? null;
  const selColor = sel.color ?? first?.color ?? null;
  const sizes = sortSizes([...new Set(variants.map((v) => v.size))]);
  const colors = [...new Set(variants.map((v) => v.color))];
  const find = (size, color) => variants.find((v) => v.size === size && v.color === color);
  const current = find(selSize, selColor);
  const onSale = p.sale_price && Number(p.sale_price) < Number(p.regular_price);

  function pickSize(size) {
    let color = selColor;
    if (!find(size, color)?.available) color = variants.find((v) => v.size === size && v.available)?.color ?? color;
    setSel({ size, color });
    setAdded(false);
  }
  function pickColor(color) {
    let size = selSize;
    if (!find(size, color)?.available) size = variants.find((v) => v.color === color && v.available)?.size ?? size;
    setSel({ size, color });
    setAdded(false);
  }
  async function add() {
    if (!current?.available) return;
    setBusy(true);
    const ok = await addToCart(current.uuid, qty);
    setBusy(false);
    if (ok) setAdded(true);
  }

  return (
    <div className="container page">
      <Breadcrumbs items={[{ label: "Home", to: "/" }, { label: "Shop", to: "/shop" }, { label: p.category, to: `/shop?category=${p.category_slug}` }, { label: p.name }]} />
      <div className="detail">
        <div className="detail-media">
          <ProductImage src={p.image} name={p.name} seed={p.category_slug} eager />
          <div className="pcard-badges">
            {p.is_new_collection && <span className="badge badge-new">New</span>}
            {onSale && <span className="badge badge-sale">−{p.discount_percentage}%</span>}
          </div>
        </div>

        <div className="detail-info">
          <Link to={`/shop?category=${p.category_slug}`} className="eyebrow-link">{p.category}</Link>
          <h1>{p.name}</h1>
          <p className="price price-lg">
            <strong>{money(p.price)}</strong>
            {onSale && <s>{money(p.regular_price)}</s>}
            {onSale && <span className="save">Save {money(Number(p.regular_price) - Number(p.price))}</span>}
          </p>
          {p.short_description && <p className="lead">{p.short_description}</p>}

          {variants.length > 0 ? (
            <>
              <div className="opt">
                <p className="opt-label">Size <span className="muted">{selSize}</span></p>
                <div className="opt-row" role="radiogroup" aria-label="Size">
                  {sizes.map((s) => {
                    const ok = variants.some((v) => v.size === s && v.available);
                    return (
                      <button key={s} type="button" role="radio" aria-checked={selSize === s} disabled={!ok} className={`chip-opt ${selSize === s ? "is-on" : ""}`} onClick={() => pickSize(s)}>{s}</button>
                    );
                  })}
                </div>
              </div>
              <div className="opt">
                <p className="opt-label">Colour <span className="muted">{selColor}</span></p>
                <div className="opt-row" role="radiogroup" aria-label="Colour">
                  {colors.map((c) => {
                    const ok = variants.some((v) => v.color === c && v.available);
                    return (
                      <button key={c} type="button" role="radio" aria-checked={selColor === c} aria-label={c} title={c} disabled={!ok} className={`swatch ${selColor === c ? "is-on" : ""}`} style={{ "--c": colorHex(c) }} onClick={() => pickColor(c)}>
                        <span />
                      </button>
                    );
                  })}
                </div>
              </div>

              <p className={`stock ${current?.available ? "in" : "out"}`}>
                {current?.available ? <><Check size={16} /> In stock</> : "This combination is out of stock"}
              </p>

              <div className="buy-row">
                <Stepper value={qty} onChange={setQty} max={10} />
                <button type="button" className="btn btn-primary btn-lg grow" disabled={!current?.available || busy} onClick={add}>
                  <ShoppingBag size={18} /> {busy ? "Adding…" : current?.available ? "Add to cart" : "Unavailable"}
                </button>
              </div>
              {added && <Alert type="success">Added to your cart.</Alert>}
            </>
          ) : (
            <Alert type="error">This product has no purchasable options right now.</Alert>
          )}

          <ul className="assure">
            <li><Banknote size={18} /> Cash on delivery — pay when it arrives</li>
            <li><Truck size={18} /> Delivery {money(config.delivery_charge_inside_dhaka)} inside Dhaka, {money(config.delivery_charge_outside_dhaka)} outside</li>
          </ul>

          {p.description && (
            <div className="desc">
              <h2>Details</h2>
              <p>{p.description}</p>
            </div>
          )}
        </div>
      </div>
      <Related product={p} />
    </div>
  );
}
