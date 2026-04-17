from django.shortcuts import render,redirect
from django.conf import settings
# Create your views here.
from store.models import Product,Category,Cart,Tax,CartOrder,CartOrderItem,Coupon,Notification,Review,Wishlist
from store.serializer import ProductSerializer,CategorySerializer,CartSerializer,CartOrderSerializer,CartOrderItemSerializer,CouponSerializer,NotificationSerializer,ReviewSerializer,WishlistSerializer
from rest_framework.response import Response
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework import generics,status
from userauths.models import User
from decimal import Decimal
import stripe
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


class OrdersAPIView(generics.ListAPIView):
    serializer_class=CartOrderSerializer
    permission_classes=[AllowAny]

    def get_queryset(self):
        user_id=self.kwargs["user_id"]
        user=User.objects.get(id=user_id)

        orders=CartOrder.objects.filter(buyer=user,payment_status="paid")

        return orders
    

class OrdersDetailAPIView(generics.RetrieveAPIView):
    serializer_class=CartOrderSerializer
    permission_classes=[AllowAny]

    def get_object(self):
        user_id=self.kwargs["user_id"]
        order_oid=self.kwargs["order_oid"]

        user=User.objects.get(id=user_id)

        order=CartOrder.objects.get(buyer=user,oid=order_oid,payment_status="paid")

        return order





class WishlistAPIView(generics.ListCreateAPIView):
    serializer_class=WishlistSerializer
    throttle_classes=[]
    permission_classes=[AllowAny]

    def get_queryset(self):
        user_id=self.kwargs["user_id"]

        user=User.objects.get(id=user_id)
        wishlists=Wishlist.objects.filter(user=user)

        return wishlists
    

    def create(self, request, *args, **kwargs):
        payload=request.data

        product_id=payload["product_id"]
        user_id=payload["user_id"]

        product=Product.objects.get(id=product_id)
        user=User.objects.get(id=user_id)
        wishlist=Wishlist.objects.filter(product=product,user=user)

        if wishlist:
            wishlist.delete()
            return Response({"message":"Wishlist Deleted Successfully"},status=status.HTTP_200_OK)
        else:
            Wishlist.objects.create(product=product,user=user)
            return Response({"message":"Added to Wishlist"},status=status.HTTP_201_CREATED)
        



class CustomerNotification(generics.ListAPIView):
    serializer_class=NotificationSerializer
    permission_classes=[AllowAny]
    throttle_classes=[]


    def get_queryset(self):
        user_id=self.kwargs["user_id"]

        user=User.objects.get(id=user_id)

        return Notification.objects.filter(user=user,seen=False)
    

class MarkCustomerNotificationAsSeen(generics.RetrieveAPIView):

    serializer_class=NotificationSerializer
    permission_classes=[AllowAny]
    throttle_classes=[]


    def get_object(self):
        user_id=self.kwargs["user_id"]
        noti_id=self.kwargs["noti_id"]

        user=User.objects.get(id=user_id)
        noti=Notification.objects.get(id=noti_id,user=user)

        if noti.seen != True :
            noti.seen=True
            noti.save()
        
        return noti
