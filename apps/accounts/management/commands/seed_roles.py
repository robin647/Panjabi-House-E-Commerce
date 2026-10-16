"""
Creates the baseline staff Groups referenced in the architecture doc
(Catalog Manager, Order Manager, Inventory Manager) so granular admin
permissions can be assigned from day one. Safe to re-run.
"""

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create baseline staff permission groups."

    GROUPS = ["Catalog Manager", "Order Manager", "Inventory Manager", "Customer Support"]

    def handle(self, *args, **options):
        for name in self.GROUPS:
            _, created = Group.objects.get_or_create(name=name)
            self.stdout.write(self.style.SUCCESS(f"{'Created' if created else 'Exists'}: {name}"))
