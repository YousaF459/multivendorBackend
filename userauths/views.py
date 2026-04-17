from django.shortcuts import render
from rest_framework_simplejwt.views import TokenObtainPairView
from userauths.serializer import RegisterSerializer,LoginSerializer,PasswordResetEmailSerializer,ProfileSerializer,ChangePasswordSerializer
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework.throttling import UserRateThrottle,AnonRateThrottle,ScopedRateThrottle
from userauths.models import User,UserEmailVerification,Profile
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from django.utils.encoding import force_bytes,force_str
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import send_mail
from backend.settings import EMAIL_HOST_USER
from django.conf import settings
import random
from datetime import timedelta
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils import timezone
from userauths.throttlerates import OTPResendThrottle,LoginAttemptThrottle,PasswordResetThrottle,RegistrationThrottle
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from backend.settings import DEFAULT_FROM_EMAIL
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from vendor.models import Vendor
from django.utils.text import slugify
# Create your views here.


class LoginView(TokenObtainPairView):
    throttle_classes=[LoginAttemptThrottle]
    serializer_class = LoginSerializer
    


    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.user
        if not user or not user.is_active:
            return Response({"detail": "Invalid credentials or user deleted"}, status=status.HTTP_401_UNAUTHORIZED)

        data = serializer.validated_data  
        access = data.get("access")
        refresh = data.get("refresh")

        response = Response({"message": "Login successful"}, status=status.HTTP_200_OK)

        # Set refresh cookie
        response.set_cookie(
            key="refresh",
            value=refresh,
            httponly=True,
            secure=True,
            samesite="None",
            max_age=60 * 60 * 24 * 1,  # 7 days
            path="/"
        )

        # Set access cookie  
        response.set_cookie(
            key="access",
            value=access,
            httponly=True,
            secure=True,
            samesite="None", 
            max_age=60 * 2,  # 15 minutes
            path="/"
        )

        return response

class RegisterView(generics.CreateAPIView):
    
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    throttle_classes=[RegistrationThrottle]
    serializer_class = RegisterSerializer
    

    def perform_create(self, serializer):
        user= serializer.save()

        user.is_verified = True
        user.save()
        
        Vendor.objects.create(
        user=user,
        name=user.username,
        mobile=user.phone,     # Or any default name you prefer
        slug=f"{slugify(user.username)}-{user.id}"
        )



        
       
        return Response({"success":True,'message':"User Registered Successfully"},status=status.HTTP_201_CREATED)



    

#user clicked on logout button adn we removed access adn refresh token from cookies
#and send refresh token to blacklist it from backend

class LogoutView(APIView):
    def post(self, request):
        
        try:
            refresh_token = request.COOKIES.get("refresh")
            
            if refresh_token:
                try:
                    token = RefreshToken(refresh_token)
                    token.blacklist()
                except Exception as token_error:
                    print(token_error)
                    pass
            
            response = Response(
                {"msg": "Logout Successful"},
                status=status.HTTP_205_RESET_CONTENT
            )


            
            # Clear cookies - MUST match exactly how they were set in login
            response.delete_cookie(
                key="access",
                path="/",
                samesite="None"
                # Add domain=request.get_host() if needed for cross-subdomain
            )
            
            # Clear refresh cookie - match set_cookie attributes exactly
            response.delete_cookie(
                key="refresh",
                path="/",
                samesite="None"
                # Add domain=request.get_host() if needed
            )

            
            return response
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)



### Sending email with uidb64 and token to email
class PasswordResetEmail(APIView):
    permission_classes=(AllowAny,)
    throttle_classes=[PasswordResetThrottle]

    def post(self,request):
        serializer = PasswordResetEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
         
        uidb64=serializer.context["uidb64"] 
        token=serializer.context["token"]
        user=serializer.context["user"]

        reset_link = f"http://localhost:5173/reset-password/confirm/{uidb64}/{token}"

   

        subject = "Password Reset Request"
        message = f"Hello {user.username},\n\nPlease click the link below to reset your password:\n{reset_link}"
        recipient_list = [serializer.validated_data['email']]

        send_mail(
        subject,
        message,
        DEFAULT_FROM_EMAIL,           # sender
        recipient_list,         # replace with your email
        fail_silently=False,
        )
        

        # Normally, send email instead of returning
        return Response({"success":True,
            "message": "Password reset link generated.",
            "reset_link": reset_link
        }, status=status.HTTP_200_OK)




## passwrod reset confiramtion and new passwrod saving
class PasswordResetConfirm(APIView):
    permission_classes=(AllowAny,)
    
    def post(self,request):

        uidb64=request.data.get('uidb64')
        token=request.data.get('token')
        newPassword=request.data.get('newPassword')
        confirmPassword=request.data.get('confirmPassword')

        if newPassword != confirmPassword:
            return Response({"success":False,"error": "Passwords do not match"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            uid=force_str(urlsafe_base64_decode(uidb64))
            user=User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({"success":False,"error": "Invalid user ID"}, status=status.HTTP_400_BAD_REQUEST)
        
        token_checker=PasswordResetTokenGenerator()

        if not token_checker.check_token(user,token):
            return Response({"success":False,"error": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)
        
        user.set_password(newPassword)
        user.save()

        return Response({"success":True,"message": "Password reset successful"}, status=status.HTTP_200_OK)







class UserProfileView(APIView):
    permission_classes=[IsAuthenticated]


    def get(self,request):
        profile=request.user.profile
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)



    def patch(self, request):
        profile = request.user.profile
        serializer = ProfileSerializer(profile, data=request.data, partial=True)  # partial update
        if serializer.is_valid():
            serializer.save()
         
            return Response(serializer.data, status=status.HTTP_200_OK)
       
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    





### cahgne user passwrod from isnide
class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({"old_password": "Wrong password."}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({"detail": "Password updated successfully."}, status=status.HTTP_200_OK)
    



#### Delete account view
class DeleteAccountView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user


        refresh_token = request.COOKIES.get("refresh")
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except Exception:
                pass

        user.delete() 
        
        
        response = Response(
            {"success": True, "message": "Your account has been deleted."},
            status=status.HTTP_200_OK
        )
         # This will also delete the Profile if on_delete=models.CASCADE
        response.delete_cookie(
            key="access",
            path="/",
            samesite="None"
        )
        response.delete_cookie(
            key="refresh",
            path="/",
            samesite="None"
        )

        return response
    




class VerifyOTPView(APIView):
    permission_classes=(AllowAny,)
    
    def post(self,request):
        email=request.data.get('email')
        otp=request.data.get('otp')

        if not email or not otp:
            return Response( {"success":False,"message": "Email and OTP are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
        try:
            verification=UserEmailVerification.objects.filter(
                otp=otp,is_used=False,user__email=email
            ).latest("created_at")
        except UserEmailVerification.DoesNotExist:
            return Response(
                {"success":False,"message": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST
            )
        
        if verification.expires_at<timezone.now():
            return Response(
                {"success":False,"message": "OTP expired"}, status=status.HTTP_400_BAD_REQUEST
            )
        
        verification.is_used=True
        verification.save()

        user = verification.user
        user.is_verified = True
        user.save()

        return Response(
            {"success":True,"message": "Email verified successfully"},
            status=status.HTTP_200_OK
        )
    


class ResendOTPView(APIView):

    throttle_classes=[OTPResendThrottle]
    permission_classes=(AllowAny,)
    
    def post(self, request):
        email = request.data.get("email")

        if not email:
            return Response(
                {"success":False,"message": "Email is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"success":False,"message": "User with this email does not exist"},
                status=status.HTTP_404_NOT_FOUND
            )

        if user.is_verified:
            return Response(
                {"success":True,"code": "USER_ALREADY_VERIFIED","message": "User is already verified"},
        status=status.HTTP_200_OK )

        # Invalidate old OTPs
        UserEmailVerification.objects.filter(user=user, is_used=False).update(is_used=True)

        # Create new OTP
        verification = UserEmailVerification.objects.create(
            user=user,
            expires_at=timezone.now() + timedelta(minutes=5),
        )

        # Send email
        subject = "Your OTP Verification Code"
        message = f"""
        Hello {user.username},

        Your OTP code is: {verification.otp}
        It will expire in 5 minutes.

        If you didn’t request this, you can ignore this email.
        """
        recipient_list = [email]

        send_mail(
        subject,
        message,
        'yk05701@gmail.com',           # sender
        recipient_list,         # replace with your email
        fail_silently=False,
        )
        

        return Response(
            {"success":True, "code": "OTP_SENT","message": "New OTP sent successfully"},
            status=status.HTTP_200_OK
        )
    


class CookieTokenRefreshView(TokenRefreshView):
    throttle_classes=[] 
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get("refresh")
        if not refresh_token:
            return Response({"detail": "Refresh token missing"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            serializer = self.get_serializer(data={"refresh": refresh_token})
            serializer.is_valid(raise_exception=True)
        except TokenError:
            return Response({"detail": "Invalid or expired refresh"}, status=status.HTTP_401_UNAUTHORIZED)

        data = serializer.validated_data
        response = Response(data, status=status.HTTP_200_OK)

        # always set new access token
        response.set_cookie(
            key="access",
            value=data["access"],
            httponly=True,
            secure=True,
            samesite="None",
            max_age=60 * 2,
            path="/"
        )

        # set new refresh token if rotated
        if "refresh" in data:
            response.set_cookie(
                key="refresh",
                value=data["refresh"],
                httponly=True,
                secure=True,
                samesite="None",
                max_age=60 * 60 * 24,
                path="/"
            )

            # blacklist old refresh token safely
            try:
                old_token = RefreshToken(refresh_token)
                old_token.blacklist()
            except Exception:
                # ignore if already blacklisted
                pass

        return response

class CheckAuthView(APIView):
    permission_classes = (AllowAny,)
    throttle_classes=[]

    def get(self, request):
        refresh_token = request.COOKIES.get("refresh")
        if not refresh_token:
            return Response({"isLoggedIn": False})

        try:
            # just validate the refresh token without blacklisting it
            RefreshToken(refresh_token)
        except TokenError:
            return Response({"isLoggedIn": False})

        return Response({"isLoggedIn": True})
    


class UserData(APIView):
    permission_classes = (AllowAny,)
    throttle_classes=[]

    def get(self, request):
        user = request.user

        if user.is_anonymous:
            return Response(
                {"msg": "No ID Found"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        return Response(
            {"id": user.id, "msg": "Successful"},
            status=status.HTTP_200_OK
        )
    



class VendorData(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes=[]  # user must be logged in via cookie

    def get(self, request):
        user = request.user

        vendor_id = None
        if hasattr(user, 'vendor'):
            vendor_id = user.vendor.id

        return Response({
            "user": {
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "vendor_id": vendor_id
            }
        })





        

class ProfileView(generics.RetrieveUpdateAPIView):
    permission_classes=[AllowAny]
    serializer_class=ProfileSerializer
    throttle_classes=[]

    def get_object(self):
        user_id=self.kwargs["user_id"]

        user=User.objects.get(id=user_id)
        profile=Profile.objects.get(user=user)

        return profile
    

