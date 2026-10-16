from django.db import models
from django.db.models import F, Q
from django.utils.text import slugify

from apps.core.models import BaseModel


class Category(BaseModel):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "name"]
        verbose_name_plural = "categories"
        indexes = [models.Index(fields=["is_active", "display_order"])]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class ProductQuerySet(models.QuerySet):
    def published(self):
        return self.filter(is_active=True, is_published=True)

    def with_main_price(self):
        # `sort_price` mirrors the Product.effective_price *property* (sale
        # price when set, else regular price) but as a DB-level annotation
        # for filtering/sorting. Deliberately NOT named effective_price:
        # Django tries to assign annotated columns onto the model instance
        # as attributes, which crashes against a read-only @property of the
        # same name (no setter) - this is why the name differs.
        return self.annotate(
            sort_price=models.Case(
                models.When(sale_price__isnull=False, then=F("sale_price")),
                default=F("regular_price"),
                output_field=models.DecimalField(max_digits=12, decimal_places=2),
            )
        )


class Product(BaseModel):
    sku = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(blank=True)
    short_description = models.CharField(max_length=300, blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    regular_price = models.DecimalField(max_digits=12, decimal_places=2)
    sale_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cost_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )  # admin-only, never serialized to customers
    image = models.ImageField(upload_to="products/", null=True, blank=True)
    is_featured = models.BooleanField(default=False)
    is_new_collection = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_published = models.BooleanField(default=True)

    objects = ProductQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_active", "is_published"]),
            models.Index(fields=["category", "is_active", "is_published"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(sale_price__isnull=True) | Q(sale_price__lt=F("regular_price")),
                name="sale_price_must_be_less_than_regular_price",
            ),
            models.CheckConstraint(condition=Q(regular_price__gte=0), name="regular_price_non_negative"),
        ]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def effective_price(self):
        return self.sale_price if self.sale_price is not None else self.regular_price

    @property
    def discount_percentage(self):
        if self.sale_price is None or self.regular_price == 0:
            return 0
        return round((1 - (self.sale_price / self.regular_price)) * 100)

    @property
    def total_stock(self):
        return sum(v.stock_quantity for v in self.variants.all() if v.is_active)


class ProductVariant(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    sku = models.CharField(max_length=80, unique=True)
    size = models.CharField(max_length=20)
    color = models.CharField(max_length=40)
    stock_quantity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["size", "color"]
        constraints = [models.UniqueConstraint(fields=["product", "size", "color"], name="unique_variant_per_product")]
        indexes = [models.Index(fields=["product", "is_active"])]

    def __str__(self) -> str:
        return f"{self.product.name} - {self.size}/{self.color}"

    @property
    def label(self) -> str:
        return f"{self.size} / {self.color}"
