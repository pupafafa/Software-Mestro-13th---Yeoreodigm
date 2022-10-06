from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
#기본 패스워드 검증도구

from rest_framework import serializers
from rest_framework.authtoken.models import Token #token model
from rest_framework.validators import UniqueValidator # to prevent duplicate email, use unique validator

from django.contrib.auth import authenticate
from .models import Profile

class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())],
    )
    password = serializers.CharField(
        write_only=True,
        required = True,
        validators = [validate_password],
    )
    password2 = serializers.CharField(write_only=True,required=True)

    class Meta:
        model = User
        fields = ('username','password','password2','email')
    
    def vaildate(self,data):
        if data['password'] !=data['password2']:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."}
            )
        return data
    
    def create(self,validated_data):
        #create 메소드 오버라이딩, 유저를 생성하고 토근을 생성하게 함
        user = User.objects.create_user(
            username = validated_data['username'],
            email=validated_data['email'],
        )
        user.set_password(validated_data['password'])
        user.save()
        token = Token.objects.create(user=user)
        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True,write_only=True)
    #write only option을 사용하면, client->Server 방향의 역직렬화만 가능

    def validate(self, data):
        user = authenticate(**data)
        if user:
            token = Token.objects.get(user=user)
            return token
        raise serializers.ValidationError(
            {"error":"Unable to log in with provided credentials"}
        )

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ("nickname","position","subjects","image")