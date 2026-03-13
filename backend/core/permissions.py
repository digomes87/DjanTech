from rest_framework.permissions import BasePermission


class IsAnalystOrAdmin(BasePermission):
    message = "Only analyst or administrators can perfom this action."

    def has_permission(self, request, _view):
        _ = _view
        return request.user.is_authenticated and request.user.role in [
            "analyst",
            "admin",
        ]


class IsOwnerOrAnalyst(BasePermission):
    """Object-level:  owner of the object or analyst"""

    def has_object_permission(self, request, _view, _obj):
        _ = (_view, _obj)
        if request.user.role in ["analyst", "admin"]:
            return True
