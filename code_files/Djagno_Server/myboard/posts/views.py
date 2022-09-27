from rest_framework import viewsets

from users.models import Profile
from .models import Photodigm, Post, UserImage
from .permissions import CustomReadOnly
from .serializers import ImageSerializer, PhotodigmSerializer, PostSerializer,PostCreateSerializer

from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

#이미지 처리를 위한 라이브러리 로드
from PIL import Image
from django.conf import settings
from io import BytesIO
from django.core.files.base import ContentFile
#from django.core.files.uploadedfile import InMemoryUploadedFile

#svg 변환 라이브러리
import cairosvg

class PostAPIView(APIView):
    frame_coordinate = [(34,110),(322,110),(34,472),(322,472)]
    def get(self,request):
        posts = Post.objects.filter(is_public=True)
        serializer = PostSerializer(posts,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)

    def post(self,request):
        serializer = PostCreateSerializer(data=request.data)
        image_list = request.FILES.getlist('image')
        photo_frame = Image.open(settings.MEDIA_ROOT+'/frame.png')
        print('image_list: ',image_list)
        if serializer.is_valid():
            post = serializer.save()
        for idx, img in enumerate(image_list): 
            
            print('이미지 타입은?? ', type(img),img)
            
            image = UserImage.objects.create(post=post,image=img)
            
            
            
            now_img = Image.open(img).resize((260,340))
            now_img.show()
            
            photo_frame.paste(now_img,self.frame_coordinate[idx])
            photo_frame.seek(0)
            
        image_io = BytesIO()
        photo_frame.save(image_io,format='png')
        print(ContentFile(image_io.getvalue()))
        photodigm = Photodigm.objects.create(post=post)
        photodigm.photodigm.save('tmp.png',ContentFile(image_io.getvalue()))
        photodigm.save()
        # photo_frame.seek(0)
        photo_frame.show()
        print('request : ',request)
        print("*"*20)
        print('request.data : ',request.data)
        print("*"*20)
        print('request.file : ',request.FILES)
        print("*"*20)

         
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status = status.HTTP_201_CREATED)
        return Response(serializer.errors,status = status.HTTP_400_BAD_REQUEST)

class UserImageAPIView(APIView):
    def get(self,reqeust):
        img = UserImage.objects.all()
        serializer = ImageSerializer(img,many=True)
        return Response(data=serializer.data,status=status.HTTP_200_OK)

class PhotodigmAPIView(APIView):
    def get(self,request):
        photodigm = Photodigm.objects.all()
        serializer = PhotodigmSerializer(photodigm,many=True)
        return Response(data=serializer.data,status=status.HTTP_200_OK)