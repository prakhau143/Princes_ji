
from django.db import models
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator

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
	is_active = models.BooleanField(default=True)

	def __str__(self):
		return self.name

# Product model
class Product(models.Model):
	name = models.CharField(max_length=200)
	description = models.TextField(blank=True)
	price = models.DecimalField(max_digits=10, decimal_places=2)
	cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
	image = models.ImageField(upload_to='products/', blank=True, null=True)  # Main image
	stock = models.PositiveIntegerField(default=0)
	low_stock_threshold = models.PositiveIntegerField(default=5)
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

	def hover_image_url(self):
		first_extra = self.additional_images.first()
		if first_extra and first_extra.image:
			return first_extra.image.url
		if self.image:
			return self.image.url
		return None

	def first_video_url(self):
		first_video = self.videos.first()
		if first_video and first_video.video:
			return first_video.video.url
		return None


# Product Additional Images (max 4 images per product including main)
class ProductImage(models.Model):
	product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='additional_images')
	image = models.ImageField(upload_to='products/additional/')
	is_primary = models.BooleanField(default=False)
	sort_order = models.PositiveIntegerField(default=0)
	created_at = models.DateTimeField(auto_now_add=True)
	
	class Meta:
		ordering = ['sort_order', 'created_at']
	
	def __str__(self):
		return f"Image for {self.product.name}"


class ProductVideo(models.Model):
	product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='videos')
	video = models.FileField(upload_to='products/videos/')
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['created_at']

	def __str__(self):
		return f"Video for {self.product.name}"


# Order model

class Order(models.Model):
	STATUS_CHOICES = [
		('pending', 'Pending'),
		('processing', 'Processing'),
		('shipped', 'Shipped'),
		('delivered', 'Delivered'),
		('rto', 'RTO / Returned to Origin'),
		('returned', 'Returned by Customer'),
		('refund_pending', 'Refund Pending'),
		('refund_completed', 'Refund Completed'),
		('cancelled', 'Cancelled'),
	]
	
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
	total = models.DecimalField(max_digits=10, decimal_places=2)
	shipping_address = models.TextField(default='Address not provided')
	shipping_city = models.CharField(max_length=100, default='City not provided')
	shipping_state = models.CharField(max_length=100, default='State not provided')
	shipping_postal_code = models.CharField(max_length=20, default='00000')
	shipping_country = models.CharField(max_length=100, default='Country not provided')
	mobile_number = models.CharField(max_length=20, blank=True)
	assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_orders')

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
		('exquisite', 'Exquisite Collection'),
		('owners_fav', "Owner's Favourites"),
	]
	
	section_type = models.CharField(max_length=20, choices=SECTION_CHOICES)
	product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='homepage_sections')
	position = models.PositiveIntegerField(default=1, help_text="Position in section (1-4)")
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	
	class Meta:
		ordering = ['section_type', 'position']
		verbose_name = "Homepage Section Product"
		verbose_name_plural = "🏠 Homepage Product Sections"
	
	def __str__(self):
		return f"{self.get_section_type_display()} - Position {self.position}: {self.product.name}"
	
	def clean(self):
		from django.core.exceptions import ValidationError
		if self.position < 1:
			raise ValidationError({'position': 'Position must be 1 or higher.'})


class InstagramReel(models.Model):
	title = models.CharField(max_length=200, blank=True)
	video = models.FileField(upload_to='reels/', blank=True, null=True)
	video_url = models.URLField(blank=True, help_text="Optional external video URL (Instagram/CDN)")
	thumbnail = models.ImageField(upload_to='reels/thumbnails/', blank=True, null=True)
	is_active = models.BooleanField(default=True)
	sort_order = models.PositiveIntegerField(default=0)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['sort_order', '-created_at']
		verbose_name = "Instagram Reel"
		verbose_name_plural = "🎥 Instagram Reels"

	def __str__(self):
		return self.title or f"Reel #{self.id}"

	def get_video_source(self):
		if self.video:
			return self.video.url
		return self.video_url


class WishlistItem(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist_items')
	product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlisted_by')
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		unique_together = ['user', 'product']
		ordering = ['-created_at']
		verbose_name = "Wishlist Item"
		verbose_name_plural = "💗 Wishlist Items"

	def __str__(self):
		return f"{self.user.username} → {self.product.name}"


class ProductReview(models.Model):
	product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='product_reviews')
	order_item = models.OneToOneField('OrderItem', on_delete=models.CASCADE, null=True, blank=True, related_name='review')
	reviewer_name = models.CharField(max_length=120, blank=True)
	reviewer_image = models.ImageField(upload_to='reviewers/', blank=True, null=True)
	rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
	title = models.CharField(max_length=200, blank=True)
	body = models.TextField(blank=True)
	is_approved = models.BooleanField(default=False)
	is_visible = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_at']
		verbose_name = "Product Review"
		verbose_name_plural = "⭐ Product Reviews"

	def __str__(self):
		return f"{self.product.name} ({self.rating}/5)"


class ProductVariant(models.Model):
	product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
	name = models.CharField(max_length=80, help_text="e.g. Size M / Gold / 2gm")
	price_delta = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	stock = models.PositiveIntegerField(default=0)
	is_active = models.BooleanField(default=True)
	sort_order = models.PositiveIntegerField(default=0)

	class Meta:
		ordering = ['sort_order', 'id']
		verbose_name = "Product Variant"
		verbose_name_plural = "🧩 Product Variants"

	def __str__(self):
		return f"{self.product.name} - {self.name}"


class TrustBadge(models.Model):
	title = models.CharField(max_length=120)
	subtitle = models.CharField(max_length=200, blank=True)
	icon_image = models.ImageField(upload_to='trust_badges/', blank=True, null=True)
	is_active = models.BooleanField(default=True)
	sort_order = models.PositiveIntegerField(default=0)

	class Meta:
		ordering = ['sort_order', 'id']
		verbose_name = "Trust Badge"
		verbose_name_plural = "🛡️ Trust Badges"

	def __str__(self):
		return self.title


class MarketingSpend(models.Model):
	SOURCE_CHOICES = [
		('meta', 'Meta (Facebook/Instagram)'),
		('google', 'Google Ads'),
		('influencer', 'Influencer'),
		('other', 'Other'),
	]
	source = models.CharField(max_length=30, choices=SOURCE_CHOICES, default='meta')
	campaign = models.CharField(max_length=120, blank=True)
	amount = models.DecimalField(max_digits=10, decimal_places=2)
	spend_date = models.DateField()
	notes = models.CharField(max_length=255, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-spend_date', '-created_at']
		verbose_name = "Marketing Spend"
		verbose_name_plural = "📣 Marketing Spend"

	def __str__(self):
		return f"{self.get_source_display()} ₹{self.amount} ({self.spend_date})"


class ExpenseEntry(models.Model):
	CATEGORY_CHOICES = [
		('shipping', 'Shipping'),
		('packaging', 'Packaging'),
		('salary', 'Salary'),
		('rent', 'Rent'),
		('tools', 'Tools/Software'),
		('other', 'Other'),
	]
	category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='other')
	title = models.CharField(max_length=120)
	amount = models.DecimalField(max_digits=10, decimal_places=2)
	expense_date = models.DateField()
	notes = models.CharField(max_length=255, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-expense_date', '-created_at']
		verbose_name = "Expense Entry"
		verbose_name_plural = "🧾 Expense Ledger"

	def __str__(self):
		return f"{self.title} ₹{self.amount} ({self.expense_date})"


class HomepageSectionContent(models.Model):
	SECTION_CHOICES = [
		('hero', 'Hero Section'),
		('launch_featured_media', 'New Launch + Featured Shared Media'),
		('exquisite_collection', 'Exquisite Collection'),
		('account_cards_media', 'Orders + Cart + Profile Shared Media'),
		('instagram_reels', 'Instagram Reels Slider'),
	]
	section_key = models.CharField(max_length=50, choices=SECTION_CHOICES, unique=True)
	title = models.CharField(max_length=200, blank=True)
	subtitle = models.TextField(blank=True)
	button_text = models.CharField(max_length=80, blank=True)
	button_url = models.CharField(max_length=255, blank=True)
	secondary_button_text = models.CharField(max_length=80, blank=True)
	secondary_button_url = models.CharField(max_length=255, blank=True)
	background_image = models.ImageField(upload_to='homepage_sections/', blank=True, null=True)
	background_video = models.FileField(upload_to='homepage_sections/videos/', blank=True, null=True)
	is_active = models.BooleanField(default=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['section_key']
		verbose_name = "Homepage Section Content"
		verbose_name_plural = "🎨 Homepage Section Content"

	def __str__(self):
		return self.get_section_key_display()


class OrderLifecycleLog(models.Model):
	EVENT_TYPE_CHOICES = [
		('status_change', 'Status Change'),
		('assignment', 'Assignment'),
		('internal_note', 'Internal Note'),
		('rto_update', 'RTO Update'),
		('refund_update', 'Refund Update'),
	]
	order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='lifecycle_logs')
	event_type = models.CharField(max_length=30, choices=EVENT_TYPE_CHOICES, default='internal_note')
	previous_status = models.CharField(max_length=30, blank=True)
	new_status = models.CharField(max_length=30, blank=True)
	note = models.TextField(blank=True)
	created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_lifecycle_logs')
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_at']
		verbose_name = "Order Lifecycle Log"
		verbose_name_plural = "🕒 Order Lifecycle Logs"

	def __str__(self):
		return f"Order #{self.order_id} - {self.event_type}"


class EditorialMedia(models.Model):
	MEDIA_TYPES = [('image', 'Image'), ('video', 'Video')]
	media_type = models.CharField(max_length=5, choices=MEDIA_TYPES, default='image')
	file = models.FileField(upload_to='editorial/')
	product = models.ForeignKey(
		'Product', on_delete=models.SET_NULL, null=True, blank=True,
		related_name='editorial_media',
		help_text='Redirect to this product when clicked',
	)
	order = models.PositiveIntegerField(default=0, help_text='Sort order (lower = first)')
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['order', 'created_at']
		verbose_name = 'Editorial Media'
		verbose_name_plural = '🗞️ Editorial Gallery'

	def __str__(self):
		return f"{self.get_media_type_display()} — {self.file.name}"


class HeroSlide(models.Model):
	background_image = models.ImageField(upload_to='hero/', blank=True, null=True)
	background_video = models.FileField(upload_to='hero/videos/', blank=True, null=True)
	heading = models.CharField(max_length=200, blank=True)
	subheading = models.TextField(blank=True)
	button_text = models.CharField(max_length=80, blank=True)
	button_url = models.CharField(max_length=255, blank=True)
	order = models.PositiveIntegerField(default=0)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['order', 'created_at']
		verbose_name = "Hero Slide"
		verbose_name_plural = "🖼️ Hero Slides"

	def __str__(self):
		return self.heading or f"Slide #{self.id}"


class SiteSettings(models.Model):
	glass_flash_enabled = models.BooleanField(
		default=False,
		help_text="Enable animated shine/gloss reflection effect on all product images"
	)

	class Meta:
		verbose_name = "Site Settings"
		verbose_name_plural = "⚙️ Site Settings"

	def __str__(self):
		return "Site Settings"

	@classmethod
	def get_settings(cls):
		obj, _ = cls.objects.get_or_create(pk=1)
		return obj
