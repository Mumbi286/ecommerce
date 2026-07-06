from django.db import models
from django.utils.text import slugify
from django.urls import reverse

# Create your models here.
class Product(models.Model):
    
    def get_absolute_url(self):
        return reverse('detail',args=(self.slug,))

    


    name = models.CharField(max_length=100)
    price = models.FloatField()
    description = models.TextField()
    image = models.ImageField(upload_to='images/')
    slug = models.SlugField(unique=True,blank=True)
    stock = models.IntegerField()
    active = models.BooleanField()


    def save(self,*args,**kwargs):
        if not self.slug:
            # self.slug =  slugify(self.name)
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter+=1
            self.slug = slug
        super().save(*args,**kwargs)





