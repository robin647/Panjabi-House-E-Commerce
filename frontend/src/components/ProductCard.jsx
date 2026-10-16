import { Link } from "react-router-dom";
import { money } from "../lib/format";
import ProductImage from "./ProductImage";

export default function ProductCard({ product: p }) {
  const onSale = p.sale_price && Number(p.sale_price) < Number(p.regular_price);
  return (
    <Link to={`/product/${p.slug}`} className={`pcard ${p.in_stock ? "" : "is-soldout"}`}>
      <div className="pcard-media">
        <ProductImage src={p.image} name={p.name} seed={p.category_slug} />
        <div className="pcard-badges">
          {p.is_new_collection && <span className="badge badge-new">New</span>}
          {onSale && <span className="badge badge-sale">−{p.discount_percentage}%</span>}
        </div>
        {!p.in_stock && <span className="pcard-soldout">Sold out</span>}
      </div>
      <div className="pcard-body">
        <span className="pcard-cat">{p.category}</span>
        <h3 className="pcard-name">{p.name}</h3>
        <p className="price">
          <strong>{money(p.price)}</strong>
          {onSale && <s>{money(p.regular_price)}</s>}
        </p>
      </div>
    </Link>
  );
}

export function ProductCardSkeleton() {
  return (
    <div className="pcard" aria-hidden="true">
      <div className="pcard-media skeleton" />
      <div className="pcard-body">
        <span className="skeleton skel-line short" />
        <span className="skeleton skel-line" />
        <span className="skeleton skel-line short" />
      </div>
    </div>
  );
}

export function ProductGrid({ products, loading, count = 8 }) {
  if (loading && !products?.length) {
    return (
      <div className="grid-products">
        {Array.from({ length: count }, (_, i) => (
          <ProductCardSkeleton key={i} />
        ))}
      </div>
    );
  }
  return (
    <div className="grid-products">
      {products.map((p) => (
        <ProductCard key={p.uuid} product={p} />
      ))}
    </div>
  );
}
