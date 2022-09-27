

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from users.models import Profile

from PIL import Image
from django.conf import settings

class Post(models.Model):
    # author = models.ForeignKey(User,on_delete=models.CASCADE,related_name='posts')
    # profile = models.ForeignKey(Profile,on_delete=models.CASCADE,blank=True)
    # likes = models.ManyToManyField(User,related_name='like_posts',blank=True)
    title = models.CharField(max_length=128)
    category = models.CharField(max_length=128)
    body = models.TextField()
    published_date = models.DateTimeField(default=timezone.now)
    is_public = models.BooleanField(default=True)
    #image = models.ImageField(upload_to = 'post/',default='default.png')
    # image2 = models.ImageField(upload_to = 'post/',default='default.png')
    # image3 = models.ImageField(upload_to = 'post/',default='default.png')
    # image4 = models.ImageField(upload_to = 'post/',default='default.png')

    # def save(self,*args,**kwargs):
    #     super().save()
    #     photo_frame = Image.open(settings.MEDIA_ROOT+'/frame.png')
    #     photo_frame.show()
    #     print(self.image)
    #     print(self.image.path)

        # for img in self.image:
        #     print(img)
        # img = Image.open(self.image.path)
        # img.show()
        # img2 = Image.open(self.image2.path)
        # img3 = Image.open(self.image3.path)
        # img4 = Image.open(self.image4.path)
        # resize_img1 = img1.resize((260,340))
        # resize_img2 = img2.resize((260,340))
        # resize_img3 = img3.resize((260,340))
        # resize_img4 = img4.resize((260,340))
        # photo_frame.paste(resize_img1,(34,110))
        # photo_frame.paste(resize_img2,(322,110))
        # photo_frame.paste(resize_img3,(34,472))
        # photo_frame.paste(resize_img4,(322,472))
        # photo_frame.show()
        # photo_frame.save(self.image1.path)
        
class UserImage(models.Model):
    post = models.ForeignKey(Post,blank=False,null=False,on_delete=models.CASCADE)
    image = models.ImageField(upload_to='post/',default='default.png')

class Photodigm(models.Model):
    post = models.OneToOneField(Post,on_delete=models.CASCADE,primary_key=True)
    photodigm = models.ImageField(upload_to='post/photodigm/',default='default.png')