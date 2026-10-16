import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import ProductCard from "../components/ProductCard";
import ProductImage from "../components/ProductImage";
import { Pagination, Stepper } from "../components/ui";

const product = {
  uuid: "1", name: "Slim Fit Blazer", slug: "slim-fit-blazer", category: "Blazer", category_slug: "blazer",
  regular_price: "4500.00", sale_price: "3999.00", price: "3999.00", discount_percentage: 11, image: null,
  is_new_collection: true, in_stock: true,
};

describe("ProductCard", () => {
  it("links to the product and shows sale pricing and badges", () => {
    render(<MemoryRouter><ProductCard product={product} /></MemoryRouter>);
    expect(screen.getByRole("link", { name: /Slim Fit Blazer/ })).toHaveAttribute("href", "/product/slim-fit-blazer");
    expect(screen.getByText("৳3,999")).toBeInTheDocument();
    expect(screen.getByText("৳4,500")).toBeInTheDocument();
    expect(screen.getByText("−11%")).toBeInTheDocument();
    expect(screen.getByText("New")).toBeInTheDocument();
  });
  it("marks sold-out products", () => {
    render(<MemoryRouter><ProductCard product={{ ...product, in_stock: false }} /></MemoryRouter>);
    expect(screen.getByText("Sold out")).toBeInTheDocument();
  });
});

describe("ProductImage", () => {
  it("renders a designed placeholder when there is no photo", () => {
    render(<ProductImage name="Wedding Sherwani" seed="sherwani" />);
    expect(screen.getByRole("img", { name: "Wedding Sherwani" })).toHaveClass("art");
  });
  it("falls back to the placeholder if the photo fails to load", () => {
    render(<ProductImage src="/media/missing.jpg" name="Koti" seed="koti" />);
    fireEvent.error(screen.getByRole("img", { name: "Koti" }));
    expect(screen.getByRole("img", { name: "Koti" })).toHaveClass("art");
  });
});

describe("Stepper", () => {
  it("respects min/max and reports changes", () => {
    const onChange = vi.fn();
    const { rerender } = render(<Stepper value={1} onChange={onChange} max={3} />);
    expect(screen.getByLabelText("Decrease quantity")).toBeDisabled();
    fireEvent.click(screen.getByLabelText("Increase quantity"));
    expect(onChange).toHaveBeenCalledWith(2);
    rerender(<Stepper value={3} onChange={onChange} max={3} />);
    expect(screen.getByLabelText("Increase quantity")).toBeDisabled();
  });
});

describe("Pagination", () => {
  it("renders nothing for a single page", () => {
    const { container } = render(<Pagination page={1} totalPages={1} onChange={() => {}} />);
    expect(container).toBeEmptyDOMElement();
  });
  it("collapses long ranges and navigates", () => {
    const onChange = vi.fn();
    render(<Pagination page={5} totalPages={10} onChange={onChange} />);
    expect(screen.getByLabelText("Page 5")).toHaveAttribute("aria-current", "page");
    expect(screen.queryByLabelText("Page 8")).not.toBeInTheDocument();
    fireEvent.click(screen.getByText("Next"));
    expect(onChange).toHaveBeenCalledWith(6);
  });
});
