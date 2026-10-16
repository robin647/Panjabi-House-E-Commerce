"""
Seeds a small demo catalog (categories, products, variants with real stock)
so the storefront isn't an empty shell on first run. Idempotent - safe to
re-run; existing rows are matched by slug/sku and skipped.
"""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalog.models import Category, Product, ProductVariant

CATEGORIES = [
    {"name": "Panjabi", "description": "Traditional and modern Panjabis for every occasion."},
    {"name": "Sherwani", "description": "Formal sherwanis for weddings and celebrations."},
    {"name": "Koti", "description": "Waistcoats to layer over Panjabis and shirts."},
    {"name": "Blazer", "description": "Smart blazers for formal and semi-formal wear."},
    {"name": "Shirt", "description": "Casual and formal shirts."},
]

SIZES = ["S", "M", "L", "XL"]
COLORS = ["Black", "White", "Navy"]

PRODUCTS = [
    {
        "category": "Panjabi",
        "name": "Premium Embroidered Panjabi",
        "sku": "PJ-EMB-001",
        "regular_price": "2200.00",
        "sale_price": "1899.00",
        "is_featured": True,
        "is_new_collection": True,
        "short_description": "Hand-embroidered cotton panjabi.",
    },
    {
        "category": "Panjabi",
        "name": "Classic Cotton Panjabi",
        "sku": "PJ-CLS-002",
        "regular_price": "1500.00",
        "sale_price": None,
        "is_featured": False,
        "is_new_collection": False,
        "short_description": "Everyday comfort cotton panjabi.",
    },
    {
        "category": "Panjabi",
        "name": "Linen Summer Panjabi",
        "sku": "PJ-LIN-003",
        "regular_price": "1800.00",
        "sale_price": None,
        "is_featured": False,
        "is_new_collection": True,
        "short_description": "Breathable linen, perfect for summer.",
    },
    {
        "category": "Sherwani",
        "name": "Wedding Sherwani Set",
        "sku": "SW-WED-001",
        "regular_price": "8500.00",
        "sale_price": "7499.00",
        "is_featured": True,
        "is_new_collection": False,
        "short_description": "Full sherwani set with churidar.",
    },
    {
        "category": "Koti",
        "name": "Embroidered Koti Waistcoat",
        "sku": "KT-EMB-001",
        "regular_price": "1200.00",
        "sale_price": None,
        "is_featured": False,
        "is_new_collection": True,
        "short_description": "Layer it over any panjabi.",
    },
    {
        "category": "Blazer",
        "name": "Slim Fit Formal Blazer",
        "sku": "BL-SLM-001",
        "regular_price": "4500.00",
        "sale_price": "3999.00",
        "is_featured": True,
        "is_new_collection": False,
        "short_description": "Tailored slim-fit blazer.",
    },
    {
        "category": "Shirt",
        "name": "Oxford Formal Shirt",
        "sku": "SH-OXF-001",
        "regular_price": "1100.00",
        "sale_price": None,
        "is_featured": False,
        "is_new_collection": False,
        "short_description": "Crisp Oxford weave, full sleeve.",
    },
    {
        "category": "Shirt",
        "name": "Casual Check Shirt",
        "sku": "SH-CHK-002",
        "regular_price": "950.00",
        "sale_price": "799.00",
        "is_featured": False,
        "is_new_collection": True,
        "short_description": "Relaxed fit check shirt.",
    },
]


class Command(BaseCommand):
    help = "Seed demo categories, products and stocked variants."

    def handle(self, *args, **options):
        with transaction.atomic():
            categories = {}
            for i, cat in enumerate(CATEGORIES):
                obj, created = Category.objects.get_or_create(
                    name=cat["name"], defaults={"description": cat["description"], "display_order": i}
                )
                categories[cat["name"]] = obj
                self.stdout.write(self.style.SUCCESS(f"{'Created' if created else 'Exists'} category: {obj.name}"))

            for p in PRODUCTS:
                product, created = Product.objects.get_or_create(
                    sku=p["sku"],
                    defaults={
                        "name": p["name"],
                        "category": categories[p["category"]],
                        "regular_price": Decimal(p["regular_price"]),
                        "sale_price": Decimal(p["sale_price"]) if p["sale_price"] else None,
                        "short_description": p["short_description"],
                        "description": p["short_description"]
                        + " Made with quality materials and finished for daily wear.",
                        "is_featured": p["is_featured"],
                        "is_new_collection": p["is_new_collection"],
                    },
                )
                self.stdout.write(self.style.SUCCESS(f"{'Created' if created else 'Exists'} product: {product.name}"))

                if created:
                    for size in SIZES:
                        for color in COLORS:
                            ProductVariant.objects.get_or_create(
                                product=product,
                                size=size,
                                color=color,
                                defaults={"sku": f"{product.sku}-{size}-{color[:3].upper()}", "stock_quantity": 15},
                            )

        self.stdout.write(self.style.SUCCESS("Catalog seed complete."))
