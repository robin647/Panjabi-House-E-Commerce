from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.db.models import Q

from apps.core.models import BaseModel
from apps.core.utils import normalize_email, normalize_phone


class Role(models.TextChoices):
    CUSTOMER = "customer", "Customer"
    STAFF = "staff", "Staff"
    ADMIN = "admin", "Admin"
    SUPER_ADMIN = "super_admin", "Super Admin"


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create(self, *, email=None, phone_number=None, password=None, **extra_fields):
        email = normalize_email(email)
        phone_number = normalize_phone(phone_number) if phone_number else None
        if not email and not phone_number:
            raise ValueError("A user requires an email or a phone number.")
        user = self.model(email=email, phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.full_clean(exclude=["password"])
        user.save(using=self._db)
        return user

    def create_user(self, email=None, phone_number=None, password=None, **extra_fields):
        extra_fields.setdefault("role", Role.CUSTOMER)
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create(email=email, phone_number=phone_number, password=password, **extra_fields)

    def create_superuser(self, email=None, phone_number=None, password=None, **extra_fields):
        extra_fields.setdefault("role", Role.SUPER_ADMIN)
        extra_fields["is_staff"] = True
        extra_fields["is_superuser"] = True
        if extra_fields.get("is_staff") is not True or extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_staff=True and is_superuser=True.")
        return self._create(email=email, phone_number=phone_number, password=password, **extra_fields)


class User(BaseModel, AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CUSTOMER, db_index=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(email__isnull=False) | Q(phone_number__isnull=False),
                name="user_requires_email_or_phone",
            )
        ]
        indexes = [models.Index(fields=["role", "is_active"])]

    def __str__(self) -> str:
        return self.email or self.phone_number or str(self.uuid)

    def get_full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip() or (self.email or self.phone_number or "")

    def get_short_name(self) -> str:
        return self.first_name or self.get_full_name()

    @property
    def is_customer(self) -> bool:
        return self.role == Role.CUSTOMER

    @property
    def is_staff_role(self) -> bool:
        return self.role in (Role.STAFF, Role.ADMIN, Role.SUPER_ADMIN)
