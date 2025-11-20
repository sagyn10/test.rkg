# Конфигурация автоматической API документации

## drf-spectacular

Проект использует **drf-spectacular** для автоматической генерации OpenAPI 3.0 документации.

### Установка

```bash
pip install drf-spectacular
```

### Конфигурация в settings.py

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # DRF
    'rest_framework',
    'rest_framework_simplejwt',
    
    # API Documentation
    'drf_spectacular',
    
    # Your apps
    'blog_api',
]

REST_FRAMEWORK = {
    # Схема для автоматической документации
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    
    # Аутентификация
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'blog_api.authentication.CustomJWTAuthentication',
    ),
    
    # Пагинация
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
}

# Настройки drf-spectacular
SPECTACULAR_SETTINGS = {
    'TITLE': 'Blog API',
    'DESCRIPTION': 'REST API для блога с постами и комментариями. '
                   'Поддерживает JWT аутентификацию, CRUD операции для постов '
                   'и комментариев с гибкой системой прав доступа.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    
    # Настройки UI
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
    },
    
    # Схема аутентификации
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': r'/api/v[0-9]',
}
```

### Настройка URL маршрутов (urls.py)

```python
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/v1/', include('blog_api.urls')),
    
    # OpenAPI Schema (JSON/YAML)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    
    # Swagger UI - интерактивная документация
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    # ReDoc - альтернативная документация
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
```

### Документирование ViewSets

#### Базовое документирование

```python
from rest_framework import viewsets
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

class PostViewSet(viewsets.ModelViewSet):
    """
    API эндпоинты для управления постами блога.
    
    list: Получить список всех постов (с пагинацией)
    create: Создать новый пост
    retrieve: Получить детали конкретного поста
    update: Обновить пост полностью
    partial_update: Обновить пост частично
    destroy: Удалить пост
    """
    queryset = Post.objects.all()
    serializer_class = PostSerializer
```

#### Расширенное документирование с декораторами

```python
class PostViewSet(viewsets.ModelViewSet):
    """ViewSet для управления постами"""
    
    @extend_schema(
        summary="Получить список постов",
        description="Возвращает пагинированный список всех постов. "
                    "Гости видят только опубликованные посты.",
        responses={200: PostListSerializer(many=True)},
        parameters=[
            OpenApiParameter(
                name='page',
                type=int,
                location=OpenApiParameter.QUERY,
                description='Номер страницы для пагинации'
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        summary="Создать новый пост",
        description="Создает новый пост. Требует аутентификации. "
                    "Автор устанавливается автоматически.",
        request=PostSerializer,
        responses={
            201: PostSerializer,
            401: OpenApiResponse(description='Не авторизован'),
            400: OpenApiResponse(description='Невалидные данные'),
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
```

#### Документирование custom actions

```python
class PostViewSet(viewsets.ModelViewSet):
    """ViewSet для постов"""
    
    @extend_schema(
        request=CommentSerializer,
        responses={
            201: CommentSerializer,
            400: OpenApiResponse(description='Невалидные данные'),
            401: OpenApiResponse(description='Требуется аутентификация'),
        },
        description="Добавить комментарий к посту. Требует JWT токен.",
        summary="Добавить комментарий"
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def comments(self, request, pk=None):
        """POST /api/v1/posts/{id}/comments/ - добавить комментарий"""
        post = self.get_object()
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(post=post, author=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
```

### Документирование Serializers

```python
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

class PostSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Post.
    
    Поля:
    - id: Уникальный идентификатор поста
    - title: Заголовок поста
    - body: Содержимое поста
    - author: Информация об авторе (только чтение)
    - created_at: Дата создания (только чтение)
    - updated_at: Дата обновления (только чтение)
    - is_published: Опубликован ли пост
    """
    
    author = UserSerializer(read_only=True)
    
    @extend_schema_field(serializers.IntegerField)
    def get_comments_count(self, obj):
        """Количество комментариев к посту"""
        return obj.comments.count()
    
    class Meta:
        model = Post
        fields = '__all__'
```

### Документирование аутентификации

```python
from drf_spectacular.utils import extend_schema
from rest_framework_simplejwt.views import TokenObtainPairView

class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Получение JWT токена для аутентификации.
    
    Отправьте username и password для получения access и refresh токенов.
    Access токен используется в заголовке Authorization: Bearer <token>
    """
    serializer_class = CustomTokenObtainPairSerializer
    
    @extend_schema(
        summary="Получить JWT токены",
        description="Аутентификация пользователя и получение JWT токенов. "
                    "Access токен действителен 1 час, refresh токен - 1 день.",
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'access': {'type': 'string'},
                    'refresh': {'type': 'string'},
                    'user_id': {'type': 'integer'},
                    'username': {'type': 'string'},
                }
            },
            401: OpenApiResponse(description='Неверные учетные данные'),
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
```

### Генерация схемы в файл

Экспортировать OpenAPI схему:

```bash
# YAML формат
python manage.py spectacular --color --file schema.yml

# JSON формат
python manage.py spectacular --format openapi-json --file schema.json
```

### Проверка схемы

```bash
# Валидация схемы
python manage.py spectacular --validate

# Вывод в консоль
python manage.py spectacular --color
```

## Доступ к документации

После запуска сервера (`python manage.py runserver`):

- **Swagger UI**: http://127.0.0.1:8000/api/docs/
- **ReDoc**: http://127.0.0.1:8000/api/redoc/
- **OpenAPI Schema**: http://127.0.0.1:8000/api/schema/

## Использование в Swagger UI

1. Откройте http://127.0.0.1:8000/api/docs/
2. Зарегистрируйте пользователя: `POST /api/v1/users/`
3. Получите токен: `POST /api/v1/auth/token/`
4. Нажмите кнопку **"Authorize"** (🔒 в правом верхнем углу)
5. Введите: `Bearer YOUR_ACCESS_TOKEN`
6. Нажмите "Authorize" и "Close"
7. Теперь все защищенные эндпоинты доступны для тестирования

## Импорт в Postman

1. Скачайте схему: http://127.0.0.1:8000/api/schema/
2. Откройте Postman
3. File → Import → Выберите скачанный файл
4. Все эндпоинты будут импортированы в коллекцию

## Дополнительные возможности

### Теги и группировка

```python
class PostViewSet(viewsets.ModelViewSet):
    """ViewSet для постов"""
    
    @extend_schema(tags=['Posts'])
    def list(self, request):
        pass
    
    @extend_schema(tags=['Comments'])
    @action(detail=True, methods=['post'])
    def comments(self, request, pk=None):
        pass
```

### Примеры в документации

```python
from drf_spectacular.utils import OpenApiExample

@extend_schema(
    examples=[
        OpenApiExample(
            'Пример создания поста',
            value={
                'title': 'Мой первый пост',
                'body': 'Содержимое поста',
                'is_published': True
            },
            request_only=True,
        ),
    ]
)
def create(self, request):
    pass
```

### Скрытие эндпоинтов

```python
from drf_spectacular.utils import extend_schema

@extend_schema(exclude=True)
def internal_method(self, request):
    """Этот метод не будет показан в документации"""
    pass
```

## Полезные ссылки

- [drf-spectacular документация](https://drf-spectacular.readthedocs.io/)
- [OpenAPI Specification](https://swagger.io/specification/)
- [Swagger UI](https://swagger.io/tools/swagger-ui/)
- [ReDoc](https://github.com/Redocly/redoc)
