from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import User, Post, Comment
from .serializers import UserSerializer, PostSerializer, PostListSerializer, CommentSerializer
from .permissions import IsAuthorOrReadOnly, IsAuthenticatedOrReadOnlyPublished
from .authentication import CustomTokenObtainPairSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    """Кастомный view для получения JWT токена"""
    serializer_class = CustomTokenObtainPairSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления пользователями.
    Регистрация доступна всем, остальное - только авторизованным.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return [IsAuthenticated()]


class PostViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления постами.
    
    Гости могут видеть только опубликованные посты (is_published=True).
    Авторизованные пользователи могут создавать посты и видеть все.
    Редактировать/удалять может только автор.
    """
    queryset = Post.objects.all().select_related('author').prefetch_related('comments')
    permission_classes = [IsAuthenticatedOrReadOnlyPublished]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PostListSerializer
        return PostSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Гости видят только опубликованные посты
        if not self.request.user or not self.request.user.is_authenticated:
            queryset = queryset.filter(is_published=True)
        return queryset
    
    def perform_create(self, serializer):
        # Автоматически устанавливаем текущего пользователя как автора
        serializer.save(author=self.request.user)
    
    @extend_schema(
        request=CommentSerializer,
        responses={201: CommentSerializer},
        description="Добавить комментарий к посту"
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def comments(self, request, pk=None):
        """
        POST /api/v1/posts/{id}/comments/ - добавить комментарий к посту
        """
        post = self.get_object()
        serializer = CommentSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(post=post, author=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        responses={200: CommentSerializer(many=True)},
        description="Получить список комментариев к посту"
    )
    @comments.mapping.get
    def get_comments(self, request, pk=None):
        """
        GET /api/v1/posts/{id}/comments/ - получить список комментариев
        """
        post = self.get_object()
        comments = post.comments.all().select_related('author')
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)


class CommentViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления комментариями.
    Редактировать/удалять может только автор комментария.
    """
    queryset = Comment.objects.all().select_related('author', 'post')
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, IsAuthorOrReadOnly]
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

