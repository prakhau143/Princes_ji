
from django.db import models
from django.conf import settings

class Cart(models.Model):
	user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"Cart for {self.user.username}"

class CartItem(models.Model):
	cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
	product = models.ForeignKey('Product', on_delete=models.CASCADE)
	quantity = models.PositiveIntegerField(default=1)
	added_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"{self.quantity} x {self.product.name}"
from django.db import models

# Create your models here.

from django.contrib.auth.models import User

class UserProfile(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE)
	# Add additional fields as needed, e.g. address, phone, etc.
	address = models.CharField(max_length=255, blank=True)
	phone = models.CharField(max_length=20, blank=True)
	mobile = models.CharField(max_length=20, blank=True)

	def __str__(self):
		return self.user.username


# Category model
class Category(models.Model):
	name = models.CharField(max_length=100, unique=True)

	def __str__(self):
		return self.name

# Product model
class Product(models.Model):
	name = models.CharField(max_length=200)
	description = models.TextField(blank=True)
	price = models.DecimalField(max_digits=10, decimal_places=2)
	category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
	image = models.ImageField(upload_to='products/', blank=True, null=True)  # Main image
	stock = models.PositiveIntegerField(default=0)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return self.name
	
	def get_all_images(self):
		"""Returns list of all product images (main + additional)"""
		images = []
		if self.image:
			images.append(self.image.url)
		images.extend([img.image.url for img in self.additional_images.all()[:3]])
		return images[:4]  # Maximum 4 images total


# Product Additional Images (max 4 images per product including main)
class ProductImage(models.Model):
	product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='additional_images')
	image = models.ImageField(upload_to='products/additional/')
	created_at = models.DateTimeField(auto_now_add=True)
	
	class Meta:
		ordering = ['created_at']
	
	def __str__(self):
		return f"Image for {self.product.name}"


# Order model

class Order(models.Model):
	STATUS_CHOICES = [
		('pending', 'Pending'),
		('processing', 'Processing'),
		('shipped', 'Shipped'),
		('delivered', 'Delivered'),
		('cancelled', 'Cancelled'),
	]
	
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
	total = models.DecimalField(max_digits=10, decimal_places=2)
	shipping_address = models.TextField(default='Address not provided')
	shipping_city = models.CharField(max_length=100, default='City not provided')
	shipping_postal_code = models.CharField(max_length=20, default='00000')
	shipping_country = models.CharField(max_length=100, default='Country not provided')
	mobile_number = models.CharField(max_length=20, blank=True)

	def __str__(self):
		return f"Order #{self.id} by {self.user.username}"

class OrderItem(models.Model):
	order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
	product = models.ForeignKey(Product, on_delete=models.CASCADE)
	quantity = models.PositiveIntegerField()
	price = models.DecimalField(max_digits=10, decimal_places=2)

	def __str__(self):
		return f"{self.quantity} x {self.product.name}"

class Notification(models.Model):
	NOTIFICATION_TYPES = [
		('order_placed', 'New Order Placed'),
		('order_cancelled', 'Order Cancelled'),
		('low_stock', 'Low Stock Alert'),
		('new_customer', 'New Customer Registered'),
	]
	
	title = models.CharField(max_length=200)
	message = models.TextField()
	notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
	is_read = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)
	related_order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, blank=True)
	related_product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
	
	class Meta:
		ordering = ['-created_at']
	
	def __str__(self):
		return self.title

class PasswordResetOTP(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	otp = models.CharField(max_length=6)
	created_at = models.DateTimeField(auto_now_add=True)
	is_used = models.BooleanField(default=False)
	
	def __str__(self):
		return f"OTP for {self.user.username}"

# Newsletter subscription model
class NewsletterSubscriber(models.Model):
	email = models.EmailField(unique=True)
	name = models.CharField(max_length=100, blank=True)
	subscribed_at = models.DateTimeField(auto_now_add=True)
	is_active = models.BooleanField(default=True)
	source = models.CharField(max_length=50, default='Website')

	class Meta:
		ordering = ['-subscribed_at']

	def __str__(self):
		return self.email

# Contact message model
class ContactMessage(models.Model):
	name = models.CharField(max_length=100)
	email = models.EmailField()
	subject = models.CharField(max_length=200, default='General Inquiry')
	message = models.TextField()
	created_at = models.DateTimeField(auto_now_add=True)
	is_read = models.BooleanField(default=False)
	is_replied = models.BooleanField(default=False)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return f"Message from {self.name} ({self.email})"


# Announcement Bar Model
class Announcement(models.Model):
	title = models.CharField(max_length=200, blank=True, help_text="Optional announcement title")
	message = models.TextField(help_text="Announcement message (required)")
	is_active = models.BooleanField(default=True, help_text="Show this announcement on the website")
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	
	class Meta:
		ordering = ['-created_at']
		verbose_name = "Announcement Bar"
		verbose_name_plural = "📢 Announcement Bar"
	
	def __str__(self):
		return self.title if self.title else self.message[:50]


# Homepage Product Sections Model
class HomepageSectionProduct(models.Model):
	SECTION_CHOICES = [
		('most_selling', 'Most Selling Products'),
		('trending', 'Trending Products'),
		('new_launch', 'New Launch Products'),
		('featured', 'Featured Products'),
	]
	
	section_type = models.CharField(max_length=20, choices=SECTION_CHOICES)
	product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='homepage_sections')
	position = models.PositiveIntegerField(default=1, help_text="Position in section (1-4)")
	created_at = models.DateTimeField(auto_now_add=True)
	
	class Meta:
		ordering = ['section_type', 'position']
		unique_together = ['section_type', 'position']
		verbose_name = "Homepage Section Product"
		verbose_name_plural = "🏠 Homepage Product Sections"
	
	def __str__(self):
		return f"{self.get_section_type_display()} - Position {self.position}: {self.product.name}"
	
	def clean(self):
		from django.core.exceptions import ValidationError
		# Validate position is between 1 and 4
		if self.position < 1 or self.position > 4:
			raise ValidationError({'position': 'Position must be between 1 and 4.'})
		
		# Check if section already has 4 products
		existing_count = HomepageSectionProduct.objects.filter(
			section_type=self.section_type
		).exclude(pk=self.pk).count()
		
		if existing_count >= 4:
			raise ValidationError(
				f'The {self.get_section_type_display()} section already has 4 products. '
				f'Please remove one before adding a new product.'
			)
