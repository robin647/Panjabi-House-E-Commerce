import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { PackageSearch, SlidersHorizontal, X } from "lucide-react";
import { ProductGrid } from "../components/ProductCard";
import { Alert, EmptyState, Pagination } from "../components/ui";
import { api } from "../lib/api";
import { useCategories, useDocumentTitle, useFetch } from "../lib/hooks";

const SORTS = [
  ["-created_at", "Newest"],
  ["sort_price", "Price: low to high"],
  ["-sort_price", "Price: high to low"],
  ["name", "Name: A–Z"],
];
const PAGE_SIZE = 12;

export default function Shop() {
  const [sp, setSp] = useSearchParams();
  const categories = useCategories();
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [search, setSearch] = useState(sp.get("search") || "");
  const [minPrice, setMinPrice] = useState(sp.get("min_price") || "");
  const [maxPrice, setMaxPrice] = useState(sp.get("max_price") || "");

  // keep the local inputs in sync when the URL changes (back/forward, header search, chips)
  useEffect(() => {
    setSearch(sp.get("search") || "");
    setMinPrice(sp.get("min_price") || "");
    setMaxPrice(sp.get("max_price") || "");
  }, [sp]);

  const category = sp.get("category") || "";
  const onSale = sp.get("on_sale") === "true";
  const isNew = sp.get("new_collection") === "true";
  const featured = sp.get("featured") === "true";
  const ordering = sp.get("ordering") || "-created_at";
  const page = Number(sp.get("page") || 1);
  const term = sp.get("search") || "";
  const activeCategory = categories.find((c) => c.slug === category);

  useDocumentTitle(activeCategory?.name || (onSale ? "Sale" : isNew ? "New in" : "Shop"));

  const query = {
    category, search: term, ordering, page, page_size: PAGE_SIZE,
    min_price: sp.get("min_price") || "", max_price: sp.get("max_price") || "",
    on_sale: onSale ? "true" : "", new_collection: isNew ? "true" : "", featured: featured ? "true" : "",
  };
  const { data, meta, loading, error, reload } = useFetch(() => api.get("/products/", { query }), [sp.toString()]);

  function update(patch) {
    const next = new URLSearchParams(sp);
    Object.entries(patch).forEach(([k, v]) => (v === "" || v == null || v === false ? next.delete(k) : next.set(k, String(v))));
    if (!("page" in patch)) next.delete("page");
    setSp(next);
  }

  const chips = [
    category && { key: "category", label: activeCategory?.name || category },
    term && { key: "search", label: `“${term}”` },
    (sp.get("min_price") || sp.get("max_price")) && { key: "price", label: `Price ${sp.get("min_price") || 0}–${sp.get("max_price") || "∞"}` },
    onSale && { key: "on_sale", label: "On sale" },
    isNew && { key: "new_collection", label: "New in" },
    featured && { key: "featured", label: "Featured" },
  ].filter(Boolean);
  const removeChip = (key) => update(key === "price" ? { min_price: "", max_price: "" } : { [key]: "" });
  const products = data || [];

  const filterPanel = (
    <>
      <div className="filters-head">
        <h2>Filters</h2>
        <button type="button" className="icon-btn filters-close" aria-label="Close filters" onClick={() => setFiltersOpen(false)}><X size={20} /></button>
      </div>
      <fieldset>
        <legend>Category</legend>
        <button type="button" className={`filter-opt ${!category ? "is-on" : ""}`} onClick={() => update({ category: "" })}>All categories</button>
        {categories.map((c) => (
          <button key={c.uuid} type="button" className={`filter-opt ${category === c.slug ? "is-on" : ""}`} aria-pressed={category === c.slug} onClick={() => update({ category: c.slug })}>{c.name}</button>
        ))}
      </fieldset>
      <fieldset>
        <legend>Price (৳)</legend>
        <form className="price-range" onSubmit={(e) => { e.preventDefault(); update({ min_price: minPrice, max_price: maxPrice }); }}>
          <input type="number" min="0" inputMode="numeric" placeholder="Min" aria-label="Minimum price" value={minPrice} onChange={(e) => setMinPrice(e.target.value)} />
          <span>–</span>
          <input type="number" min="0" inputMode="numeric" placeholder="Max" aria-label="Maximum price" value={maxPrice} onChange={(e) => setMaxPrice(e.target.value)} />
          <button type="submit" className="btn btn-dark btn-sm">Apply</button>
        </form>
      </fieldset>
      <fieldset>
        <legend>Show only</legend>
        <label className="check"><input type="checkbox" checked={onSale} onChange={(e) => update({ on_sale: e.target.checked })} /> On sale</label>
        <label className="check"><input type="checkbox" checked={isNew} onChange={(e) => update({ new_collection: e.target.checked })} /> New collection</label>
        <label className="check"><input type="checkbox" checked={featured} onChange={(e) => update({ featured: e.target.checked })} /> Featured</label>
      </fieldset>
      {chips.length > 0 && <button type="button" className="link-btn" onClick={() => setSp(new URLSearchParams())}>Clear all filters</button>}
      <button type="button" className="btn btn-primary btn-block filters-done" onClick={() => setFiltersOpen(false)}>
        Show {meta?.count ?? ""} results
      </button>
    </>
  );

  return (
    <div className="container page">
      <header className="page-head">
        <h1>{activeCategory?.name || (onSale ? "Sale" : isNew ? "New in" : "Shop all")}</h1>
        {activeCategory?.description && <p className="muted">{activeCategory.description}</p>}
      </header>

      <div className="shop-layout">
        {filtersOpen && <div className="drawer-backdrop filters-backdrop" onClick={() => setFiltersOpen(false)} />}
        <aside className={`filters ${filtersOpen ? "is-open" : ""}`} aria-label="Filters">{filterPanel}</aside>

        <div className="shop-main">
          <div className="toolbar">
            <button type="button" className="btn btn-ghost filters-toggle" onClick={() => setFiltersOpen(true)}>
              <SlidersHorizontal size={16} /> Filters{chips.length > 0 && ` (${chips.length})`}
            </button>
            <form className="toolbar-search" role="search" onSubmit={(e) => { e.preventDefault(); update({ search: search.trim() }); }}>
              <input type="search" placeholder="Search this collection" aria-label="Search products" value={search} onChange={(e) => setSearch(e.target.value)} />
            </form>
            <label className="sort">
              <span className="sr-only">Sort by</span>
              <select value={ordering} onChange={(e) => update({ ordering: e.target.value })} aria-label="Sort by">
                {SORTS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
              </select>
            </label>
          </div>

          {chips.length > 0 && (
            <div className="chips" aria-label="Active filters">
              {chips.map((c) => (
                <button key={c.key} type="button" className="chip" onClick={() => removeChip(c.key)} aria-label={`Remove filter ${c.label}`}>
                  {c.label} <X size={14} />
                </button>
              ))}
            </div>
          )}

          {meta && <p className="muted result-count" aria-live="polite">{meta.count} {meta.count === 1 ? "product" : "products"}</p>}

          {error ? (
            <Alert>
              {error.message} <button type="button" className="link-btn" onClick={reload}>Try again</button>
            </Alert>
          ) : !loading && products.length === 0 ? (
            <EmptyState icon={PackageSearch} title="No products match" action={chips.length > 0 && <button type="button" className="btn btn-primary" onClick={() => setSp(new URLSearchParams())}>Clear filters</button>}>
              Try removing a filter or searching for something else.
            </EmptyState>
          ) : (
            <ProductGrid products={products} loading={loading} count={PAGE_SIZE} />
          )}

          <Pagination page={page} totalPages={meta?.total_pages} onChange={(p) => { update({ page: p > 1 ? p : "" }); window.scrollTo({ top: 0 }); }} />
        </div>
      </div>
    </div>
  );
}
