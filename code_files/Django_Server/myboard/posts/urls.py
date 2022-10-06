from django.urls import path
from rest_framework import routers

from posts.models import Post

from .views import  PhotodigmAPIView, PostAPIView, UserImageAPIView

# router = routers.SimpleRouter()
# router.register('posts',PostViewSet)

# urlpatterns = router.urls

urlpatterns = [
    path('posts/',PostAPIView.as_view()),
    path('posts/imgs/',UserImageAPIView.as_view()),
    path('posts/photodigms/',PhotodigmAPIView.as_view()),
]