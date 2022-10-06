from rest_framework import serializers
from users.serializers import ProfileSerializer
from .models import Photodigm, Post,UserImage


class PostCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ('title','category','body')

class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserImage
        fields = ('post','image')

class PhotodigmSerializer(serializers.ModelSerializer):
    class Meta:
        model = Photodigm
        fields = ('post','photodigm')

class PostSerializer(serializers.ModelSerializer):
    photodigm = PhotodigmSerializer(many=False,read_only=True)
    class Meta:
        model=Post
        fields = ('pk','title','body','published_date','is_public','photodigm')