from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Кастомное разрешение для постов и комментариев:
    - Только владелец может редактировать/удалять свой контент
    - Все остальные могут только читать
    """
    
    def has_object_permission(self, request, view, obj):
        # Разрешить GET, HEAD или OPTIONS запросы (только чтение)
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Разрешить изменение только автору
        return obj.author.id == request.user.id


class IsAuthenticatedOrReadOnlyPublished(permissions.BasePermission):
    """
    Гости могут видеть только опубликованные посты.
    Авторизованные пользователи могут видеть все и создавать новые.
    """
    
    def has_permission(self, request, view):
        # Разрешить чтение всем
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Создание/изменение только для авторизованных
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Если метод безопасный (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            # Гости видят только опубликованные посты
            if not request.user or not request.user.is_authenticated:
                return obj.is_published
            # Авторизованные видят все
            return True
        
        # Изменение/удаление только для автора
        return obj.author.id == request.user.id
