import { useEffect, useState } from "react";

// Curated, on-brand gradient pairs. Products without a photo get one of these
// (picked deterministically from the category/name) plus a tunic illustration,
// so a catalogue with no uploaded images still looks designed, not broken.
const GRADIENTS = [
  ["#7a1f2b", "#c2573a"],
  ["#1f3a4d", "#3b7a8c"],
  ["#3d2c5e", "#7d5ba6"],
  ["#2f4a3a", "#6b8f5e"],
  ["#8a5a2b", "#d1a45f"],
  ["#2b2b3a", "#58587a"],
];

function hash(str) {
  let h = 0;
  for (let i = 0; i < str.length; i += 1) h = (h * 31 + str.charCodeAt(i)) >>> 0;
  return h;
}

export default function ProductImage({ src, name, seed, className = "", eager = false }) {
  const [failed, setFailed] = useState(false);
  useEffect(() => setFailed(false), [src]);

  if (src && !failed) {
    return (
      <img
        className={`pimg ${className}`}
        src={src}
        alt={name}
        loading={eager ? "eager" : "lazy"}
        onError={() => setFailed(true)}
      />
    );
  }
  const [a, b] = GRADIENTS[hash(seed || name || "x") % GRADIENTS.length];
  return (
    <div className={`pimg art ${className}`} style={{ "--a": a, "--b": b }} role="img" aria-label={name}>
      <svg viewBox="0 0 120 160" aria-hidden="true" focusable="false">
        <path
          d="M40 14 60 24 80 14 108 36 98 66 84 58 86 148H34L36 58 22 66 12 36Z"
          fill="rgba(255,255,255,.14)"
          stroke="rgba(255,255,255,.65)"
          strokeWidth="2"
          strokeLinejoin="round"
        />
        <path d="M60 24V74" stroke="rgba(255,255,255,.55)" strokeWidth="2" />
        <circle cx="60" cy="38" r="2.2" fill="rgba(255,255,255,.85)" />
        <circle cx="60" cy="52" r="2.2" fill="rgba(255,255,255,.85)" />
        <circle cx="60" cy="66" r="2.2" fill="rgba(255,255,255,.85)" />
      </svg>
    </div>
  );
}
