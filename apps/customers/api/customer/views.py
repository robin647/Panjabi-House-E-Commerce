from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from apps.core.utils import api_response
from apps.customers.models import Address

from .serializers import AddressSerializer


class AddressViewSet(viewsets.ModelViewSet):
    """
    Full CRUD over the authenticated user's own addresses, object-scoped by
    queryset (not just permission checks) so another user's address 404s
    rather than 403s - consistent with this project's "don't reveal
    existence of other users' data" rule.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = AddressSerializer
    lookup_field = "uuid"

    def get_queryset(self):
        # drf-spectacular generates the schema against a fake request with
        # an AnonymousUser; filtering on that would raise, so short-circuit
        # with an empty queryset during schema generation only.
        if getattr(self, "swagger_fake_view", False):
            return Address.objects.none()
        return Address.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"], url_path="set-default")
    def set_default(self, request, uuid=None):
        address = self.get_object()
        address.is_default = True
        address.save(update_fields=["is_default"])
        return api_response(AddressSerializer(address).data, message="Default address updated.")
