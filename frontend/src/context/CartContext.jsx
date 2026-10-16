import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { errorText } from "../lib/format";
import { useAuth } from "./AuthContext";
import { useToast } from "./ToastContext";

const CartContext = createContext(null);
const EMPTY = { items: [], item_count: 0, subtotal: "0" };

export function CartProvider({ children }) {
  const { user } = useAuth();
  const [cart, setCart] = useState(EMPTY);
  const [loading, setLoading] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const refresh = useCallback(async () => {
    const r = await api.get("/cart/", { auth: true });
    setCart(r.data);
    return r.data;
  }, []);

  useEffect(() => {
    if (!user) {
      setCart(EMPTY);
      return undefined;
    }
    let alive = true;
    setLoading(true);
    api
      .get("/cart/", { auth: true })
      .then((r) => alive && setCart(r.data))
      .catch(() => {})
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, [user?.uuid]); // eslint-disable-line react-hooks/exhaustive-deps

  const apply = (r) => {
    setCart(r.data);
    return r.data;
  };
  const value = useMemo(
    () => ({
      cart,
      loading,
      drawerOpen,
      openDrawer: () => setDrawerOpen(true),
      closeDrawer: () => setDrawerOpen(false),
      refresh,
      add: (variantId, quantity = 1) => api.post("/cart/items/", { variant_id: variantId, quantity }, { auth: true }).then(apply),
      setQuantity: (itemId, quantity) => api.patch(`/cart/items/${itemId}/`, { quantity }, { auth: true }).then(apply),
      remove: (itemId) => api.delete(`/cart/items/${itemId}/`, { auth: true }).then(apply),
    }),
    [cart, loading, drawerOpen, refresh],
  );
  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

export const useCart = () => useContext(CartContext);

/** Adds a variant to the cart, sending signed-out shoppers to sign in first. */
export function useAddToCart() {
  const { user } = useAuth();
  const { add, openDrawer } = useCart();
  const { push } = useToast();
  const navigate = useNavigate();
  const location = useLocation();
  return useCallback(
    async (variantId, quantity = 1) => {
      if (!user) {
        navigate("/login", {
          state: { from: location.pathname + location.search, notice: "Sign in to add items to your cart." },
        });
        return false;
      }
      try {
        await add(variantId, quantity);
        openDrawer();
        return true;
      } catch (err) {
        push(errorText(err), "error");
        return false;
      }
    },
    [user, add, openDrawer, push, navigate, location],
  );
}
