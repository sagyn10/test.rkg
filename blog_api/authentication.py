from django.contrib.auth.hashers import check_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import exceptions
from .models import User


class CustomJWTAuthentication(JWTAuthentication):
    """
    Кастомная JWT аутентификация для работы с нашей моделью User
    """
    
    def get_user(self, validated_token):
        """
        Получаем пользователя из нашей модели User по user_id из токена
        """
        try:
            user_id = validated_token.get('user_id')
            user = User.objects.get(id=user_id)
            return user
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('User not found')


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Кастомный сериализатор для получения JWT токена с использованием нашей модели User
    """
    username_field = 'username'
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            from rest_framework_simplejwt.exceptions import AuthenticationFailed
            raise AuthenticationFailed('No active account found with the given credentials')
        
        # Проверяем пароль
        if not check_password(password, user.password):
            from rest_framework_simplejwt.exceptions import AuthenticationFailed
            raise AuthenticationFailed('No active account found with the given credentials')
        
        # Создаем токен
        refresh = self.get_token(user)
        
        data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user_id': user.id,
            'username': user.username,
        }
        
        return data
    
    @classmethod
    def get_token(cls, user):
        from rest_framework_simplejwt.tokens import RefreshToken
        
        token = RefreshToken()
        
        # Добавляем кастомные claims
        token['user_id'] = user.id
        token['username'] = user.username
        
        return token


