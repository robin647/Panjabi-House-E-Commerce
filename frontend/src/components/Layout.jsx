import { Outlet } from "react-router-dom";
import CartDrawer from "./CartDrawer";
import Footer from "./Footer";
import Header from "./Header";
import ScrollToTop from "./ScrollToTop";

export default function Layout() {
  return (
    <>
      <a className="skip-link" href="#main">Skip to content</a>
      <ScrollToTop />
      <Header />
      <main id="main">
        <Outlet />
      </main>
      <Footer />
      <CartDrawer />
    </>
  );
}
