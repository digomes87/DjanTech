from apps.accounts.serializers import UserDetailSerializer
from django.contrib.auth import get_user_model
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

User = get_user_model()


class UserViewSet(mixins.RetrieveModelMixin, GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserDetailSerializer

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        """Return the authenticated user profile"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
