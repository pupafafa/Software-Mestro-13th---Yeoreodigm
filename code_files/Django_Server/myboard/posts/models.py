

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from users.models import Profile

from PIL import Image
from django.conf import settings

class Post(models.Model):
    author = models.ForeignKey(User,on_delete=models.CASCADE,related_name='posts')
    title = models.CharField(max_length=128)
    body = models.TextField()
    published_date = models.DateTimeField(default=timezone.now)
class Photodigm(models.Model):
    post = models.OneToOneField(Post,on_delete=models.CASCADE,primary_key=True)
    photodigm = models.ImageField(upload_to='photodigm/',default='default.png')
    is_public = models.BooleanField(default=True)
class UserImage(models.Model):
    post = models.ForeignKey(Post,blank=False,null=False,on_delete=models.CASCADE)
    image = models.ImageField(upload_to='photodigm/userImage',default='default.png')
