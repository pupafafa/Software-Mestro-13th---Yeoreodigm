from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BeaseUserAdmin
from django.contrib.auth.models import User

from posts.models import Photodigm, Post, UserImage
from .models import Profile

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = "profile"

class UserAdmin(BeaseUserAdmin):
    inlines = (ProfileInline,)

admin.site.unregister(User)
admin.site.register(User,UserAdmin)
admin.site.register(Post)
admin.site.register(Photodigm)
admin.site.register(UserImage)