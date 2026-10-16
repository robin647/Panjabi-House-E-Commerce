// End-to-end: the REAL React app against a REAL running Django API (+ PostgreSQL).
// Skipped unless E2E=1. Requires: migrated DB seeded with `python manage.py seed_catalog`
// and the backend listening on TEST_API_BASE (default http://127.0.0.1:8000/api/v1).
import { describe, expect, it } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import App from "../App";
import { AuthProvider } from "../context/AuthContext";
import { CartProvider } from "../context/CartContext";
import { ToastProvider } from "../context/ToastContext";

const T = { timeout: 10000 };
const menu = () => within(document.querySelector(".menu-panel"));

function renderApp(route = "/") {
  return render(
    <MemoryRouter initialEntries={[route]}>
      <ToastProvider>
        <AuthProvider>
          <CartProvider>
            <App />
          </CartProvider>
        </AuthProvider>
      </ToastProvider>
    </MemoryRouter>,
  );
}

describe.skipIf(!process.env.E2E)("storefront against the live API", () => {
  it("browse -> sign up -> add to cart -> checkout -> track order -> sign out", async () => {
    const user = userEvent.setup();
    renderApp("/");

    // Home: hero + live featured products from the API
    expect(await screen.findByRole("heading", { name: /Dressed for every occasion/ }, T)).toBeInTheDocument();
    // (it is featured, new and on sale, so it legitimately appears in several sections)
    expect((await screen.findAllByRole("link", { name: /Premium Embroidered Panjabi/ }, T)).length).toBeGreaterThan(0);

    // Shop: category filter drives the product list
    await user.click(screen.getAllByRole("link", { name: "Shop" })[0]);
    expect(await screen.findByText(/\d+ products/, {}, T)).toBeInTheDocument();
    await user.click(await screen.findByRole("button", { name: "Koti" }, T));
    expect(await screen.findByRole("link", { name: /Embroidered Koti Waistcoat/ }, T)).toBeInTheDocument();
    await waitFor(() => expect(screen.queryByRole("link", { name: /Wedding Sherwani/ })).not.toBeInTheDocument(), T);

    // Product page, signed out -> adding to cart sends us to sign in
    await user.click(screen.getByRole("link", { name: /Embroidered Koti Waistcoat/ }));
    expect(await screen.findByRole("heading", { level: 1, name: "Embroidered Koti Waistcoat" }, T)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /Add to cart/ }));
    expect(await screen.findByText("Sign in to add items to your cart.", {}, T)).toBeInTheDocument();

    // Register through the UI; we're returned to the product we were viewing
    await user.click(screen.getByRole("link", { name: "Create an account" }));
    const email = `e2e_${Date.now()}@example.com`;
    await user.type(await screen.findByLabelText("First name"), "Nadia");
    await user.type(screen.getByLabelText("Email"), email);
    await user.type(screen.getByLabelText("Password"), "CorrectHorse9!");
    await user.type(screen.getByLabelText("Confirm password"), "CorrectHorse9!");
    await user.click(screen.getByRole("button", { name: "Create account" }));
    expect(await screen.findByRole("heading", { level: 1, name: "Embroidered Koti Waistcoat" }, T)).toBeInTheDocument();

    // Pick a size + colour and add to cart -> drawer opens with the item
    await user.click(screen.getByRole("radio", { name: "L" }));
    await user.click(screen.getByRole("radio", { name: "Navy" }));
    await user.click(screen.getByRole("button", { name: /Add to cart/ }));
    const drawer = await screen.findByRole("dialog", { name: "Shopping cart" }, T);
    expect(await within(drawer).findByText("L / Navy · ৳1,200", {}, T)).toBeInTheDocument();
    await user.click(within(drawer).getByRole("button", { name: "Increase quantity" }));
    // line total and subtotal both become ৳2,400
    await waitFor(() => expect(within(drawer).getAllByText("৳2,400")).toHaveLength(2), T);

    // Checkout: first address (Dhaka => ৳60 delivery), cash on delivery
    await user.click(within(drawer).getByRole("button", { name: "Checkout" }));
    expect(await screen.findByRole("heading", { name: "Checkout" }, T)).toBeInTheDocument();
    await user.type(await screen.findByLabelText("Full name", {}, T), "Nadia Rahman");
    await user.type(screen.getByLabelText("Phone"), "01812345678");
    await user.type(screen.getByLabelText("Address"), "House 12, Road 5, Gulshan");
    await user.type(screen.getByLabelText("Postal code"), "1212");
    await user.click(screen.getByRole("button", { name: "Save & use this address" }));
    await waitFor(() => expect(screen.getByRole("button", { name: "Place order" })).toBeEnabled(), T);
    expect(screen.getByText("৳2,460")).toBeInTheDocument(); // 2 x 1,200 + 60 delivery
    await user.click(screen.getByRole("button", { name: "Place order" }));

    // Order confirmation page
    expect(await screen.findByText(/your order is placed/, {}, T)).toBeInTheDocument();
    expect(screen.getByText(/ORD-\d{8}-\d{6}/, { selector: "h1" })).toBeInTheDocument();
    expect(screen.getAllByText("৳2,460").length).toBeGreaterThan(0);
    expect(screen.getByText("Embroidered Koti Waistcoat")).toBeInTheDocument();
    expect(screen.getByRole("list", { name: "Order progress" })).toBeInTheDocument();

    // Cart was emptied by checkout; order is in history
    await user.click(screen.getByRole("button", { name: /Open cart, 0 items/ }));
    expect(await screen.findByText("Your cart is empty")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Close cart" }));
    await user.click(screen.getByRole("button", { name: "Account menu" }));
    await user.click(menu().getByRole("link", { name: /My orders/ }));
    expect(await screen.findByRole("heading", { name: "My orders" }, T)).toBeInTheDocument();
    expect(await screen.findByText(/ORD-\d{8}-\d{6}/, {}, T)).toBeInTheDocument();

    // Saved address shows in the account area
    await user.click(screen.getByRole("button", { name: "Account menu" }));
    await user.click(menu().getByRole("link", { name: /My account/ }));
    await user.click(await screen.findByRole("tab", { name: "Addresses" }));
    expect(await screen.findByText("Nadia Rahman", {}, T)).toBeInTheDocument();

    // Sign out
    await user.click(screen.getByRole("button", { name: "Account menu" }));
    await user.click(menu().getByRole("button", { name: /Sign out/ }));
    expect(await screen.findByRole("link", { name: "Sign in" }, T)).toBeInTheDocument();
  }, 90000);

  it("rejects bad credentials with a clear message and guards private pages", async () => {
    const user = userEvent.setup();
    renderApp("/orders");
    // protected route redirects to sign-in with a notice
    expect(await screen.findByText("Please sign in to continue.", {}, T)).toBeInTheDocument();
    await user.type(screen.getByLabelText("Email or phone"), "nobody@example.com");
    await user.type(screen.getByLabelText("Password"), "WrongPassword1!");
    await user.click(screen.getByRole("button", { name: "Sign in" }));
    expect(await screen.findByRole("alert", {}, T)).toHaveTextContent("Invalid credentials.");
  }, 30000);
});
