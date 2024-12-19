from django.contrib.auth import get_user_model
from django.db import models

from .extensions import generate_unique_slug


User = get_user_model()


class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    slug = models.CharField(unique=True, blank=True, null=True, max_length=160)

    class Meta:
        verbose_name_plural = "categories"
        verbose_name = "category"
        db_table = "category"
        ordering = ["created_at"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.slug = generate_unique_slug(self, self.name)
        super().save(*args, **kwargs)


class Images(models.Model):
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to="product/")
    description = models.CharField(blank=True, null=True, max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    slug = models.CharField(unique=True, blank=True, null=True, max_length=160)

    def __str__(self):
        return self.slug

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(self, self.title)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "images"
        verbose_name = "image"
        db_table = "images"
        ordering = ["-created_at"]


class Colors(models.Model):
    color = models.CharField(max_length=100)
    description = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    slug = models.CharField(unique=True, blank=True, null=True, max_length=160)

    def __str__(self):
        return self.color

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(self, self.color)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "colors"
        verbose_name = "color"
        db_table = "colors"
        ordering = ["created_at"]


class Sizes(models.Model):
    size = models.CharField(max_length=100)
    description = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    slug = models.CharField(unique=True, blank=True, null=True, max_length=160)

    def __str__(self):
        return self.size

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.slug = generate_unique_slug(self, self.size)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "sizes"
        verbose_name = "size"
        db_table = "sizes"
        ordering = ["created_at"]


class Product(models.Model):
    title = models.CharField(max_length=200)
    category = models.ManyToManyField(Category, related_name="products")
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    slug = models.CharField(unique=True, blank=True, null=True, max_length=160)

    image = models.ManyToManyField(Images, related_name="images")
    color = models.ManyToManyField(Colors, related_name="colors")
    size = models.ManyToManyField(Sizes, related_name="sizes")

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.slug = generate_unique_slug(self, self.title)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "products"
        verbose_name = "product"
        db_table = "product"
        ordering = ["-created_at"]


class ProductComment(models.Model):
    content = models.TextField()
    rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    slug = models.CharField(unique=True, blank=True, null=True, max_length=160)

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="comments"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(
                self, str(self.user.phone_number).replace("+", "")
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.product.title} - {self.rating} - {self.content[:20]}"

    class Meta:
        verbose_name_plural = "product comments"
        verbose_name = "product comment"
        db_table = "product_comment"
        ordering = ["-created_at"]


class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    products = models.ManyToManyField(Product)
    created_at = models.DateTimeField(auto_now_add=True)
    slug = models.CharField(unique=True, blank=True, null=True, max_length=160)

    def __str__(self):
        return f"Wishlist - {self.user.phone_number} - {self.products.count()} items"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(
                self, str(self.user.phone_number).replace("+", "")
            )
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "wishlists"
        verbose_name = "wishlist"
        db_table = "wishlist"
        ordering = ["-created_at"]
