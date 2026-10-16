import { useEffect, useRef, useState } from "react";
import { api } from "./api";
import { SHOP_NAME } from "./format";

/** Runs an async loader whenever `deps` change. Keeps the previous data while reloading. */
export function useFetch(loader, deps) {
  const [state, setState] = useState({ data: null, meta: null, loading: true, error: null });
  const [tick, setTick] = useState(0);
  useEffect(() => {
    let alive = true;
    setState((s) => ({ ...s, loading: true, error: null }));
    loader()
      .then((r) => alive && setState({ data: r.data, meta: r.meta, loading: false, error: null }))
      .catch((error) => alive && setState({ data: null, meta: null, loading: false, error }));
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick]);
  return { ...state, reload: () => setTick((t) => t + 1) };
}

let categoriesPromise = null;
export function useCategories() {
  const [categories, setCategories] = useState([]);
  useEffect(() => {
    let alive = true;
    categoriesPromise ||= api
      .get("/categories/")
      .then((r) => r.data)
      .catch(() => {
        categoriesPromise = null;
        return [];
      });
    categoriesPromise.then((c) => alive && setCategories(c));
    return () => {
      alive = false;
    };
  }, []);
  return categories;
}

const DEFAULT_CONFIG = {
  currency: "BDT",
  delivery_charge_inside_dhaka: "60.00",
  delivery_charge_outside_dhaka: "120.00",
  payment_methods: ["cod"],
};
let configPromise = null;
export function useShopConfig() {
  const [config, setConfig] = useState(DEFAULT_CONFIG);
  useEffect(() => {
    let alive = true;
    configPromise ||= api
      .get("/config/")
      .then((r) => r.data)
      .catch(() => {
        configPromise = null;
        return DEFAULT_CONFIG;
      });
    configPromise.then((c) => alive && setConfig(c));
    return () => {
      alive = false;
    };
  }, []);
  return config;
}

export function useDocumentTitle(title) {
  useEffect(() => {
    document.title = title ? `${title} · ${SHOP_NAME}` : SHOP_NAME;
  }, [title]);
}

export function useLockBody(locked) {
  useEffect(() => {
    if (!locked) return undefined;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, [locked]);
}

export function useClickOutside(ref, handler, active = true) {
  const saved = useRef(handler);
  saved.current = handler;
  useEffect(() => {
    if (!active) return undefined;
    const onDown = (e) => {
      if (ref.current && !ref.current.contains(e.target)) saved.current(e);
    };
    document.addEventListener("mousedown", onDown);
    document.addEventListener("touchstart", onDown);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("touchstart", onDown);
    };
  }, [ref, active]);
}

export function useEscape(handler, active = true) {
  useEffect(() => {
    if (!active) return undefined;
    const onKey = (e) => e.key === "Escape" && handler(e);
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [handler, active]);
}
