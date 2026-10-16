# Storefront (React)

Customer-facing website for the shop: React 19, Vite, React Router, plain CSS
(no UI framework — the design system lives in `src/styles.css`), `lucide-react`
icons. Talks to the Django REST API under `/api/v1`.

```bash
npm install
npm run dev       # http://localhost:5173  (proxies /api /media /admin -> Django :8000)
npm run build     # -> dist/  (Django serves this at "/")
npm test          # unit tests;  E2E=1 npm test  adds the live full-journey test
```

## Structure

```
src/
  lib/        api.js (envelope + silent token refresh), format.js, hooks.js
  context/    AuthContext, CartContext (+ useAddToCart), ToastContext
  components/ Header, Footer, CartDrawer, CartLines, ProductCard/Image, AddressForm, ui.jsx (Field, Modal, Stepper, Pagination…)
  pages/      Home, Shop, ProductDetail, Cart, Checkout, Orders(+detail), Auth (login/register/forgot/reset), Account, NotFound
  test/       lib + component unit tests, e2e.test.jsx (live API)
```

## Behaviour worth knowing

- **Auth**: JWTs in `localStorage`; an expired access token is refreshed once
  transparently (rotating refresh token), and a failed refresh signs the user out.
- **Cart** is server-side (per account); signed-out visitors are sent to sign in
  when they add something, then returned to the product.
- **Prices/stock are never trusted from the client** — the UI only displays what
  the API returns; checkout sends an `Idempotency-Key` (reused on retry of the
  same request) so a double-click can't create two orders.
- **Shop filters live in the URL** (`/shop?category=koti&on_sale=true&page=2`),
  so every view is shareable and survives refresh/back.
- Products without photos get a designed placeholder (gradient + tunic
  illustration) — upload images in Django Admin and they appear automatically.
- **Responsive**: mobile-first CSS; filters become a bottom sheet, the header
  collapses to a menu, the cart is a slide-over drawer, and checkout stacks.
- Accessible by default: skip link, labelled controls, focus rings, ARIA on
  radio groups/dialogs/pagination, `prefers-reduced-motion` respected.

## Configuration (build time)

See `.env.example`: `VITE_SHOP_NAME`, `VITE_API_BASE`, `VITE_PROXY_TARGET`.
