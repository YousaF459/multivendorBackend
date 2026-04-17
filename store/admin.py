from django.contrib import admin
from store.models import (
    Product, Category, Gallery, Specification, Size, Color,
    Cart, CartOrder, CartOrderItem, ProductFaq, Review,
    Wishlist, Notification, Coupon,Tax
)


# ===========================
# INLINE ADMIN CONFIGURATION
# ===========================
class GalleryInline(admin.TabularInline):
    model = Gallery
    extra = 0

class SpecificationInline(admin.TabularInline):
    model = Specification
    extra = 0

class SizeInline(admin.TabularInline):
    model = Size
    extra = 0

class ColorInline(admin.TabularInline):
    model = Color
    extra = 0


# ===========================
# PRODUCT ADMIN
# ===========================
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'price', 'category', 'shipping_amount',
        'stock_qty', 'in_stock', 'vendor', 'featured',
        'status', 'rating'
    ]
    inlines = [GalleryInline, SpecificationInline, SizeInline, ColorInline]
    
    
    


# ===========================
# CATEGORY ADMIN
# ===========================
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['title', 'active']
    


# ===========================
# CART ADMIN
# ===========================
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'qty', 'total', 'date']
    


# ===========================
# CART ORDER ADMIN
# ===========================
class CartOrderAdmin(admin.ModelAdmin):
    list_display = ['oid', 'buyer', 'payment_status', 'order_status', 'total', 'date']
    


# ===========================
# CART ORDER ITEM ADMIN
# ===========================
class CartOrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'vendor', 'qty', 'total', 'date']
    


# ===========================
# PRODUCT FAQ ADMIN
# ===========================
class ProductFaqAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'question', 'active', 'date']
    


# ===========================
# REVIEW ADMIN
# ===========================
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'rating', 'active', 'date']
   


# ===========================
# WISHLIST ADMIN
# ===========================
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'date']
    


# ===========================
# NOTIFICATION ADMIN
# ===========================
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'vendor', 'order', 'order_item', 'seen', 'date']
    


# ===========================
# COUPON ADMIN
# ===========================
class CouponAdmin(admin.ModelAdmin):
    list_display = ['vendor', 'code', 'discount', 'active', 'date']
    


# ===========================
# REGISTER MODELS
# ===========================
admin.site.register(Product, ProductAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(CartOrder, CartOrderAdmin)
admin.site.register(CartOrderItem, CartOrderItemAdmin)
admin.site.register(ProductFaq, ProductFaqAdmin)
admin.site.register(Review, ReviewAdmin)
admin.site.register(Wishlist, WishlistAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(Coupon, CouponAdmin)
admin.site.register(Tax)
