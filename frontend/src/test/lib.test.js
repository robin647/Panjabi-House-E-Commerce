import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, api, setAuthLostHandler, tokenStore } from "../lib/api";
import { errorText, fieldErrors, isDhaka, money, sortSizes } from "../lib/format";

const json = (body, status = 200) => new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });

describe("format helpers", () => {
  it("formats taka without needless decimals", () => {
    expect(money("1899.00")).toBe("৳1,899");
    expect(money(60)).toBe("৳60");
    expect(money("12.5")).toBe("৳12.50");
    expect(money("abc")).toBe("—");
  });
  it("sorts clothing sizes in wearing order, unknown sizes last", () => {
    expect(sortSizes(["XL", "S", "M", "XXL", "L"])).toEqual(["S", "M", "L", "XL", "XXL"]);
    expect(sortSizes(["42", "M"])).toEqual(["M", "42"]);
  });
  it("flattens API field errors to one message per field", () => {
    const err = new ApiError("Validation failed.", { errors: { email: ["Taken."], password: { 0: "Too short" }, non_field_errors: "x" } });
    expect(fieldErrors(err)).toMatchObject({ email: "Taken.", non_field_errors: "x" });
    expect(errorText(err)).toBe("Taken.");
    expect(errorText(new ApiError("Nope"))).toBe("Nope");
  });
  it("recognises Dhaka regardless of case/spacing", () => {
    expect(isDhaka("  DHAKA ")).toBe(true);
    expect(isDhaka("Sylhet")).toBe(false);
  });
});

describe("api client", () => {
  beforeEach(() => vi.stubGlobal("fetch", vi.fn()));
  afterEach(() => vi.unstubAllGlobals());

  it("unwraps the success envelope and pagination meta", async () => {
    fetch.mockResolvedValue(json({ success: true, message: "ok", data: [1, 2], meta: { count: 2 } }));
    const r = await api.get("/products/", { query: { page: 2, search: "", on_sale: false, category: "koti" } });
    expect(r).toEqual({ data: [1, 2], meta: { count: 2 }, message: "ok" });
    expect(fetch.mock.calls[0][0]).toMatch(/\/products\/\?page=2&category=koti$/); // empty/false params dropped
  });

  it("turns error envelopes into ApiError with field errors", async () => {
    fetch.mockResolvedValue(json({ success: false, message: "Validation failed.", errors: { email: "Bad" }, code: "validation_error" }, 400));
    await expect(api.post("/auth/register/", {})).rejects.toMatchObject({ name: "ApiError", status: 400, code: "validation_error", errors: { email: "Bad" } });
  });

  it("reports an unreachable server clearly", async () => {
    fetch.mockRejectedValue(new TypeError("fetch failed"));
    await expect(api.get("/x/")).rejects.toMatchObject({ code: "network_error" });
  });

  it("refreshes an expired access token once and retries the request", async () => {
    tokenStore.set({ access: "old", refresh: "r1" });
    fetch
      .mockResolvedValueOnce(json({ success: false, message: "expired" }, 401))
      .mockResolvedValueOnce(json({ success: true, data: { access: "new", refresh: "r2" } }))
      .mockResolvedValueOnce(json({ success: true, data: { ok: true } }));
    const r = await api.get("/profile/", { auth: true });
    expect(r.data).toEqual({ ok: true });
    expect(tokenStore.get()).toEqual({ access: "new", refresh: "r2" });
    expect(fetch.mock.calls[2][1].headers.Authorization).toBe("Bearer new");
  });

  it("clears the session and notifies the app when refresh fails", async () => {
    tokenStore.set({ access: "old", refresh: "dead" });
    const lost = vi.fn();
    setAuthLostHandler(lost);
    fetch.mockResolvedValueOnce(json({}, 401)).mockResolvedValueOnce(json({ success: false }, 401));
    await expect(api.get("/profile/", { auth: true })).rejects.toMatchObject({ code: "session_expired" });
    expect(tokenStore.get()).toBeNull();
    expect(lost).toHaveBeenCalled();
  });
});
