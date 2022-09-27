from rest_framework import permissions

class CustomReadOnly(permissions.BasePermission):
    def has_object_permission(self,request,view,obj):
        #GET과 같은 safe method는 그냥 true
        if request.method in permissions.SAFE_METHODS:
            return True
        #요청으로 들어온 유저와 객체의 유저가 동일할 경우에만 true
        return obj.user == request.user
