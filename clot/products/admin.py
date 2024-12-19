from django.contrib import admin
from .models import Category, Colors, Images, Product, ProductComment, Sizes, Wishlist


admin.site.register(Product)
admin.site.register(Category)
admin.site.register(ProductComment)
admin.site.register(Wishlist)
admin.site.register(Images)
admin.site.register(Colors)
admin.site.register(Sizes)
