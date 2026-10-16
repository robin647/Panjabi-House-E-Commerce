export const SHOP_NAME = import.meta.env.VITE_SHOP_NAME || "Panjabi House";

export function money(value) {
  const n = Number(value);
  if (Number.isNaN(n)) return "—";
  return `৳${n.toLocaleString("en-US", {
    minimumFractionDigits: Number.isInteger(n) ? 0 : 2,
    maximumFractionDigits: 2,
  })}`;
}

export function formatDate(iso) {
  return new Date(iso).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}

export const STATUS_LABELS = {
  pending: "Pending",
  confirmed: "Confirmed",
  processing: "Processing",
  packed: "Packed",
  shipped: "Shipped",
  out_for_delivery: "Out for delivery",
  delivered: "Delivered",
  cancelled: "Cancelled",
  returned: "Returned",
  refunded: "Refunded",
};

// Happy-path order lifecycle, used by the progress tracker on the order page.
export const STATUS_STEPS = ["pending", "confirmed", "processing", "packed", "shipped", "out_for_delivery", "delivered"];

const first = (v) => (Array.isArray(v) ? first(v[0]) : v && typeof v === "object" ? first(Object.values(v)[0]) : v);

/** {field: "message"} from an ApiError's errors object (first message per field). */
export function fieldErrors(err) {
  const out = {};
  Object.entries(err?.errors || {}).forEach(([k, v]) => {
    const msg = first(v);
    if (msg) out[k] = String(msg);
  });
  return out;
}

/** One human sentence for an error: the first field message if any, else the API message. */
export function errorText(err) {
  const fe = Object.values(fieldErrors(err));
  return fe[0] || err?.message || "Something went wrong.";
}

export const SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL", "XXXL"];
export const sortSizes = (sizes) =>
  [...sizes].sort((a, b) => {
    const ia = SIZE_ORDER.indexOf(a.toUpperCase());
    const ib = SIZE_ORDER.indexOf(b.toUpperCase());
    return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib) || a.localeCompare(b);
  });

const COLOR_HEX = {
  black: "#1d1814", white: "#ffffff", navy: "#1f2f55", maroon: "#7a1f2b", red: "#b3261e", blue: "#2f5fa7",
  green: "#2f6b4a", olive: "#6b6b2f", grey: "#8b8b8b", gray: "#8b8b8b", beige: "#d8c7a6", cream: "#f2e8d0",
  brown: "#6b4a2f", gold: "#b8893b", pink: "#d98ba0", yellow: "#e3b73b", orange: "#d9792f", purple: "#6b3f8a",
  sky: "#8dc1e6", mustard: "#c9992b", teal: "#2b7a7a", offwhite: "#f5f1e6",
};
export const colorHex = (name) => COLOR_HEX[String(name).toLowerCase().replace(/[\s-]/g, "")] || "#cfc6b8";

export const CITY_SUGGESTIONS = [
  "Dhaka", "Chattogram", "Sylhet", "Rajshahi", "Khulna", "Barishal", "Rangpur", "Mymensingh", "Gazipur",
  "Narayanganj", "Cumilla", "Cox's Bazar",
];
export const isDhaka = (city) => String(city || "").trim().toLowerCase() === "dhaka";
