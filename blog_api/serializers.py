from rest_framework import serializers
from .models import User, Post, Comment
from django.contrib.auth.hashers import check_password


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'date_joined']
        read_only_fields = ['id', 'date_joined']
    
    def create(self, validated_data):
        user = User(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user


class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    author_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = Comment
        fields = ['id', 'post', 'author', 'author_id', 'body', 'created_at', 'updated_at', 'is_approved']
        read_only_fields = ['id', 'created_at', 'updated_at', 'post']


class PostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    comments_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = ['id', 'author', 'title', 'body', 'created_at', 'updated_at', 'is_published', 'comments', 'comments_count']
        read_only_fields = ['id', 'author', 'created_at', 'updated_at']
    
    def get_comments_count(self, obj):
        return obj.comments.count()


class PostListSerializer(serializers.ModelSerializer):
    """Упрощенный сериализатор для списка постов (без комментариев)"""
    author = UserSerializer(read_only=True)
    comments_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = ['id', 'author', 'title', 'body', 'created_at', 'updated_at', 'is_published', 'comments_count']
        read_only_fields = ['id', 'author', 'created_at', 'updated_at']
    
    def get_comments_count(self, obj):
        return obj.comments.count()
