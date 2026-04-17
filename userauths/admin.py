from django.contrib import admin
from userauths.models import Profile,User,UserEmailVerification
# Register your models here.


class UserAdmin(admin.ModelAdmin):
    list_display=['full_name','email','phone']

class ProfileAdmin(admin.ModelAdmin):
    list_display=['full_name','gender','country']
    search_fields=['full_name','date']
    list_filter=['date']

class UserEmailVerificationAdmin(admin.ModelAdmin):

     list_display=['user','otp','created_at','expires_at','is_used']




admin.site.register(User,UserAdmin)
admin.site.register(Profile,ProfileAdmin)
admin.site.register(UserEmailVerification,UserEmailVerificationAdmin)