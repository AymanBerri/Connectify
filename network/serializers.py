from rest_framework import serializers
from .models import Post, User

class UserSerializer(serializers.ModelSerializer):
    followers = serializers.StringRelatedField(many=True)
    following = serializers.StringRelatedField(many=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'followers', 'following']

class PostSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    likes_count = serializers.SerializerMethodField()
    user_has_liked = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['id', 'user', 'content', 'timestamp', 'likes_count', 'user_has_liked']

    def get_likes_count(self, obj):
        return obj.liked_by.count()

    def get_user_has_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.liked_by.filter(id=request.user.id).exists()
        return False
