from rest_framework import permissions


class IsAuthorOrAdmin(permissions.BasePermission):
    """
    Разрешает:
    - Чтение: всем
    - Создание (POST): всем авторизованным
    - Изменение/удаление: только авторам и администраторам
    """
    message = 'У вас нет прав для редактирования этого объекта.'

    def has_permission(self, request, view):
        if request.method == 'POST':
            return request.user.is_authenticated
        return True

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return (
            request.user.is_authenticated
            and (
                obj.author == request.user
                or request.user.is_staff
            )
        )


class IsAuthenticatedForMe(permissions.BasePermission):
    """
    Разрешает доступ только аутентифицированным пользователям
    для эндпоинта /me/
    """
    def has_permission(self, request, view):
        if getattr(view, 'action', None) == 'me':
            return request.user and request.user.is_authenticated
        return True
