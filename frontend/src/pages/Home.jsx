import { Link } from "react-router-dom";
import { ArrowRight, Banknote, Shirt, ShieldCheck, Truck } from "lucide-react";
import ProductImage from "../components/ProductImage";
import { ProductGrid } from "../components/ProductCard";
import { api } from "../lib/api";
import { SHOP_NAME } from "../lib/format";
import { useCategories, useDocumentTitle, useFetch, useShopConfig } from "../lib/hooks";
import { money } from "../lib/format";

function Section({ title, subtitle, to, query, count = 4 }) {
  const { data, loading, error } = useFetch(() => api.get("/products/", { query: { ...query, page_size: count } }), [JSON.stringify(query), count]);
  if (!loading && !error && !data?.length) return null;
  return (
    <section className="section container">
      <div className="section-head">
        <div>
          <h2>{title}</h2>
          {subtitle && <p className="muted">{subtitle}</p>}
        </div>
        <Link to={to} className="link-arrow">View all <ArrowRight size={16} /></Link>
      </div>
      <ProductGrid products={data || []} loading={loading} count={count} />
    </section>
  );
}

export default function Home() {
  useDocumentTitle("");
  const categories = useCategories();
  const config = useShopConfig();
  return (
    <>
      <section className="hero">
        <div className="container hero-grid">
          <div className="hero-copy">
            <span className="eyebrow">The {SHOP_NAME} collection</span>
            <h1>Dressed for every occasion.</h1>
            <p>Panjabi, sherwani, koti, blazers and shirts — made to be worn, priced honestly, and delivered to your door. Pay when it arrives.</p>
            <div className="hero-cta">
              <Link to="/shop" className="btn btn-primary btn-lg">Shop the collection</Link>
              <Link to="/shop?new_collection=true" className="btn btn-light btn-lg">See what’s new</Link>
            </div>
            <ul className="hero-points">
              <li><Banknote size={18} /> Cash on delivery</li>
              <li><Truck size={18} /> Delivery from {money(config.delivery_charge_inside_dhaka)}</li>
              <li><Shirt size={18} /> Live size &amp; colour stock</li>
            </ul>
          </div>
          <div className="hero-art" aria-hidden="true">
            <ProductImage name="Panjabi" seed="panjabi-a" className="hero-tile t1" />
            <ProductImage name="Sherwani" seed="sherwani-b" className="hero-tile t2" />
            <ProductImage name="Koti" seed="koti-c" className="hero-tile t3" />
          </div>
        </div>
      </section>

      {categories.length > 0 && (
        <section className="section container">
          <div className="section-head"><h2>Shop by category</h2></div>
          <div className="cat-grid">
            {categories.map((c) => (
              <Link key={c.uuid} to={`/shop?category=${c.slug}`} className="cat-tile">
                <ProductImage name={c.name} seed={c.slug} />
                <span className="cat-label">
                  <strong>{c.name}</strong>
                  <ArrowRight size={18} />
                </span>
              </Link>
            ))}
          </div>
        </section>
      )}

      <Section title="Featured" subtitle="Hand-picked favourites" to="/shop?featured=true" query={{ featured: "true" }} />
      <Section title="New in" subtitle="Fresh arrivals" to="/shop?new_collection=true" query={{ new_collection: "true" }} count={8} />
      <Section title="On sale" subtitle="Reduced prices while stock lasts" to="/shop?on_sale=true" query={{ on_sale: "true" }} />

      <section className="perks">
        <div className="container perks-grid">
          <div><Banknote size={26} /><h3>Cash on delivery</h3><p>Inspect your order, then pay the courier.</p></div>
          <div><Truck size={26} /><h3>Inside &amp; outside Dhaka</h3><p>Flat delivery rates, shown before you order.</p></div>
          <div><Shirt size={26} /><h3>Live availability</h3><p>Every size and colour shows what is really in stock.</p></div>
          <div><ShieldCheck size={26} /><h3>Verified checkout</h3><p>Prices and stock are re-checked when you order.</p></div>
        </div>
      </section>
    </>
  );
}
