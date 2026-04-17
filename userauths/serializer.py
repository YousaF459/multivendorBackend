from userauths.models import Profile,User,UserEmailVerification
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from django.utils.encoding import force_bytes,force_str
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
import random
from django.core.mail import send_mail
from django.conf import settings 
from django.utils import timezone
from datetime import timedelta
from django.core.validators import FileExtensionValidator





### FOR USER LOGIN

class LoginSerializer(TokenObtainPairSerializer):

    def validate(self, attrs):
        data=super().validate(attrs)

        if not self.user.is_verified:
            raise serializers.ValidationError({"message": "Please verify your email before logging in."})

        return data

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token['full_name'] = user.full_name
        token['email'] = user.email
        token['username'] = user.username

        try:
            token['vendor_id'] = user.vendor.id
        except:
            token['vendor_id'] = 0

        return token







### FOR USER REGISTRATION

class RegisterSerializer(serializers.ModelSerializer):
    password=serializers.CharField(write_only=True,required=True,validators=[validate_password])
    password2=serializers.CharField(write_only=True,required=True)

    class Meta:
        model=User
        fields=['full_name',"email",'phone','username','password','password2']




    def validate(self, attrs):
        if attrs['password']!=attrs['password2']:
            raise serializers.ValidationError({'password': ["Password does not match"]})
        return attrs
    

    def create(self, validated_data):



        user = User.objects.create(
            email=validated_data["email"],
            full_name=validated_data['full_name'],
            username=validated_data["username"],
            phone=validated_data['phone'],
            is_verified=True  # mark user as verified directly
        )

        user.set_password(validated_data['password'])

        user.save()

        return user
    


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model=User
        fields="__all__"





class ProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model=Profile
        fields="__all__"
        read_only_fields = ("user", "pid", "date")
    



    def to_representation(self, instance):
        response=super().to_representation(instance)
        response['user']=UserSerializer(instance.user).data
        return response
    


#### Password Reset Email


class PasswordResetEmailSerializer(serializers.Serializer):

    email=serializers.EmailField()

    def validate_email(self,attr):

        try:
            user=User.objects.get(email=attr)
        except User.DoesNotExist:
            raise serializers.ValidationError("No user found with this email address.")

        
        uidb64=urlsafe_base64_encode(force_bytes(user.pk))
        token=PasswordResetTokenGenerator().make_token(user)


        self.context["uidb64"] = uidb64
        self.context["token"] = token
        self.context["user"] = user

        return attr


        

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password2 = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password": "Passwords do not match."})
        return attrs