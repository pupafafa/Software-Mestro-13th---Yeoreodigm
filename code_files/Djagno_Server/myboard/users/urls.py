from django.urls import path,include
from django.contrib import admin
from .views import RegisterView,LoginView,ProfileView

from django.conf import settings


urlpatterns = [
    path('register/',RegisterView.as_view()),
    path('login/',LoginView.as_view()),
    path('profile/<int:pk>/',ProfileView.as_view()),

]

