from django.db import models
from userauths.models import User,Profile
from django.utils.text import slugify
# Create your models here.


class Vendor(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE)
    image=models.FileField(upload_to="vendor",default="vendor/vendor.png",blank=True,null=True)
    name=models.CharField(max_length=100,help_text="Shop Name",blank=True,null=True)
    description=models.TextField(blank=True,null=True)
    mobile=models.CharField(max_length=100,help_text="Shop Mobile Number",blank=True,null=True)
    active=models.BooleanField(default=True)
    date=models.DateTimeField(auto_now_add=True)
    slug=models.SlugField(unique=True,max_length=50)

    class Meta:
        verbose_name_plural="Vendors"
        ordering=["-date"]

    def __str__(self):
        return str(self.name)

    def save(self,*args,**kwargs):
        if self.slug=="" or self.slug==None:
            self.slug = slugify(self.name)
        return super().save(*args,**kwargs)
