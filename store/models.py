from django.contrib.auth.models import User
from django.db import models


class Customer(models.Model):
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, null=True)
    last_name = models.CharField(max_length=200, null=True, blank=True)
    phone = models.CharField(max_length=200, null=True, blank=True)
    email = models.CharField(max_length=200, null=True, blank=True)
    profile_picture = models.ImageField(default="default_profile_picture.png", null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    @property
    def profile_picture_url(self):
        try:
            url = self.profile_picture.url
        except ValueError:
            url = ''
        return url

    def __str__(self):
        return self.name


class Category(models.Model):
    title = models.CharField(max_length=200, verbose_name='Category')

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'

    @property
    def products(self):
        products_count = self.product_set.all().count()
        return str(products_count)

    def __str__(self):
        return self.title


class Product(models.Model):
    category = models.ForeignKey(Category, verbose_name='Category', on_delete=models.PROTECT)
    name = models.CharField(max_length=200, verbose_name='Name')
    slug = models.SlugField(unique=True)
    image = models.ImageField(verbose_name='Image', null=True, blank=True)
    description = models.TextField(verbose_name='Description', null=True)
    price = models.DecimalField(max_digits=7, decimal_places=2, verbose_name='Price')
    created_at = models.DateTimeField(auto_now_add=True)
    count_in_stock = models.IntegerField(null=True, blank=True, default=0)
    rating = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    num_reviews = models.IntegerField(null=True, blank=True, default=0)

    @property
    def imageURL(self):
        try:
            url = self.image.url
        except ValueError:
            url = ''
        return url

    def __str__(self):
        return self.name


class Review(models.Model):
    RATE_CHOICES = (
        (1, 'Poor'),
        (2, 'Fair'),
        (3, 'Good'),
        (4, 'Very Good'),
        (5, 'Excellent'),
    )

    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True)
    rating = models.PositiveSmallIntegerField(choices=RATE_CHOICES, null=True, blank=True, default=0)
    comment = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.rating)


class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True)
    date_ordered = models.DateTimeField(auto_now_add=True)
    complete = models.BooleanField(default=False)
    transaction_id = models.CharField(max_length=100, null=True)

    @property
    def get_cart_total(self):
        order_items = self.orderitem_set.all()
        total = sum([item.get_total for item in order_items])
        return total

    @property
    def get_cart_items(self):
        order_items = self.orderitem_set.all()
        total = sum([item.quantity for item in order_items])
        return total

    def __str__(self):
        return str(self.id)


class OrderItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True)
    quantity = models.IntegerField(default=0, null=True, blank=True)
    date_added = models.DateTimeField(auto_now_add=True)

    @property
    def get_total(self):
        total = self.product.price * self.quantity
        return total

    def __str__(self):
        return self.product.name


class ShippingAddress(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True)
    address = models.CharField(max_length=200, null=True)
    city = models.CharField(max_length=200, null=True)
    postal_code = models.CharField(max_length=200, null=True, blank=True)
    country = models.CharField(max_length=200, null=True, blank=True)
    shipping_price = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.address
