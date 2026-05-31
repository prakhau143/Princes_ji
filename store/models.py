
from django.db import models
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.text import slugify

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
	GENDER_CHOICES = [('M', 'Male'), ('F', 'Female'), ('O', 'Other')]

	user = models.OneToOneField(User, on_delete=models.CASCADE)
	# Legacy fields kept for compatibility
	address = models.CharField(max_length=255, blank=True)
	phone = models.CharField(max_length=20, blank=True)
	mobile = models.CharField(max_length=20, blank=True)
	# Extended personal info
	first_name = models.CharField(max_length=100, blank=True)
	last_name = models.CharField(max_length=100, blank=True)
	email = models.EmailField(blank=True)
	birthdate = models.DateField(null=True, blank=True)
	gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
	anniversary = models.DateField(null=True, blank=True)
	spouse_birthday = models.DateField(null=True, blank=True)
	kids_birthday = models.DateField(null=True, blank=True)
	occupation = models.CharField(max_length=100, blank=True)

	def __str__(self):
		return self.user.username


class CustomerProfile(models.Model):
	"""Extends User with an auto-generated 8-char customer ID and admin notes."""
	user = models.OneToOneField(
		User, on_delete=models.CASCADE, related_name='customer_profile'
	)
	customer_id = models.CharField(max_length=8, unique=True, editable=False, blank=True)
	is_enabled = models.BooleanField(default=True)          # admin can disable
	alternate_phone = models.CharField(max_length=20, blank=True)
	gstin = models.CharField(max_length=15, blank=True)
	notes = models.TextField(blank=True)

	def save(self, *args, **kwargs):
		if not self.customer_id:
			self.customer_id = self._generate_id()
		super().save(*args, **kwargs)

	@staticmethod
	def _generate_id():
		import random, string
		while True:
			letters = ''.join(random.choices(string.ascii_uppercase, k=4))
			digits  = ''.join(random.choices(string.digits, k=4))
			cid = f"{letters[:2]}{digits[:2]}{letters[2:]}{digits[2:]}"  # e.g. PR37KH2B
			if not CustomerProfile.objects.filter(customer_id=cid).exists():
				return cid

	def __str__(self):
		name = self.user.get_full_name() or self.user.username
		return f"{name} ({self.customer_id})"


class Address(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
	full_name = models.CharField(max_length=100)
	address_line1 = models.CharField(max_length=255)
	address_line2 = models.CharField(max_length=255, blank=True)
	city = models.CharField(max_length=100)
	state = models.CharField(max_length=100)
	postal_code = models.CharField(max_length=20)
	country = models.CharField(max_length=100, default='India')
	mobile = models.CharField(max_length=20)
	is_default = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-is_default', '-created_at']

	def __str__(self):
		return f"{self.full_name} — {self.city}"

	def save(self, *args, **kwargs):
		if self.is_default:
			Address.objects.filter(user=self.user, is_default=True).exclude(pk=self.pk).update(is_default=False)
		super().save(*args, **kwargs)


# Category model
class Category(models.Model):
	name = models.CharField(max_length=100, unique=True)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
	updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

	def __str__(self):
		return self.name

# Product model
class Product(models.Model):
	name = models.CharField(max_length=200)
	description = models.TextField(blank=True)
	price = models.DecimalField(max_digits=10, decimal_places=2)
	mrp = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,
		help_text="Maximum Retail Price (before discount)")
	sku = models.CharField(max_length=50, unique=True, blank=True, null=True,
		help_text="Auto-generated if left blank (e.g. PRD-000001)")
	cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0,
		help_text="Average rating (0.0 – 5.0), set directly by admin")
	rating_count = models.PositiveIntegerField(default=0,
		help_text="Total number of ratings shown on storefront")
	category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
	image = models.ImageField(upload_to='products/', blank=True, null=True)  # Main image
	stock = models.PositiveIntegerField(default=0)
	low_stock_threshold = models.PositiveIntegerField(default=5)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return self.name

	@property
	def discount_percent(self):
		if self.mrp and self.mrp > 0 and self.price < self.mrp:
			return int(round(((self.mrp - self.price) / self.mrp) * 100))
		return 0

	def save(self, *args, **kwargs):
		if not self.sku:
			import re as _re
			used = set()
			for s in Product.objects.values_list('sku', flat=True):
				if s:
					m = _re.match(r'^PRD-(\d+)$', s)
					if m:
						used.add(int(m.group(1)))
			n = 1
			while n in used:
				n += 1
			self.sku = f"PRD-{n:06d}"
		super().save(*args, **kwargs)

	def get_all_images(self):
		images = []
		if self.image:
			images.append(self.image.url)
		images.extend([img.image.url for img in self.additional_images.all()[:3]])
		return images[:4]

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
		('packed', 'Packed'),
		('shipped', 'Shipped'),
		('out_for_delivery', 'Out for Delivery'),
		('delivered', 'Delivered'),
		('rto', 'RTO / Returned to Origin'),
		('returned', 'Returned by Customer'),
		('refund_pending', 'Refund Pending'),
		('refund_completed', 'Refund Completed'),
		('cancelled', 'Cancelled'),
	]
	
	PAYMENT_METHOD_CHOICES = [
		('cod', 'Cash on Delivery'),
		('upi', 'UPI'),
		('card', 'Card'),
		('netbanking', 'Netbanking'),
	]
	PAYMENT_STATUS_CHOICES = [
		('pending', 'Pending'),
		('paid', 'Paid'),
		('failed', 'Failed'),
	]

	user = models.ForeignKey(User, on_delete=models.CASCADE)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
	total = models.DecimalField(max_digits=10, decimal_places=2)
	shipping_name = models.CharField(max_length=100, blank=True)
	shipping_address = models.TextField(default='Address not provided')
	shipping_city = models.CharField(max_length=100, default='City not provided')
	shipping_state = models.CharField(max_length=100, default='State not provided')
	shipping_postal_code = models.CharField(max_length=20, default='00000')
	shipping_country = models.CharField(max_length=100, default='Country not provided')
	mobile_number = models.CharField(max_length=20, blank=True)
	assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_orders')
	payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cod')
	payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
	razorpay_order_id = models.CharField(max_length=100, blank=True)
	razorpay_payment_id = models.CharField(max_length=100, blank=True)
	# Payment breakdown (stored at order time so they don't change if rates change later)
	coupon_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	shipping_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	cod_fee_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	# Fulfillment timestamps
	packed_at = models.DateTimeField(null=True, blank=True)
	shipped_at = models.DateTimeField(null=True, blank=True)
	out_for_delivery_at = models.DateTimeField(null=True, blank=True)
	delivered_at = models.DateTimeField(null=True, blank=True)
	# Manual order fields
	admin_notes = models.TextField(blank=True, help_text="Admin reason / notes for manual orders")
	is_manual = models.BooleanField(default=False, help_text="True if created manually by admin")

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

class UserNotification(models.Model):
	"""User-facing notifications (order updates, shipping alerts, etc.)"""
	NOTIF_TYPES = [
		('order_placed',    'Order Placed'),
		('order_updated',   'Order Updated'),
		('order_shipped',   'Order Shipped'),
		('order_delivered', 'Order Delivered'),
		('order_cancelled', 'Order Cancelled'),
		('manual_order',    'Manual Order Created'),
		('general',         'General'),
	]
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_notifications')
	title = models.CharField(max_length=200)
	message = models.TextField()
	notif_type = models.CharField(max_length=30, choices=NOTIF_TYPES, default='general')
	is_read = models.BooleanField(default=False)
	related_order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return f"[{self.user.username}] {self.title}"


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


class Collection(models.Model):
	title = models.CharField(max_length=120)
	slug = models.SlugField(unique=True)
	is_active = models.BooleanField(default=True)
	order = models.PositiveIntegerField(default=0)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['order', '-created_at']

	def __str__(self):
		return self.title

	def save(self, *args, **kwargs):
		candidate = (self.slug or self.title or "").replace('/', '-').strip()
		normalized = slugify(candidate)
		if not normalized:
			raise ValueError("Collection slug is invalid")
		self.slug = normalized
		return super().save(*args, **kwargs)


class CollectionRow(models.Model):
	POSITION_CHOICES = [('left', 'Image Left'), ('right', 'Image Right')]

	collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name='rows')
	title = models.CharField(max_length=120, blank=True)
	image = models.ImageField(upload_to='collection_rows/')
	image_position = models.CharField(max_length=5, choices=POSITION_CHOICES, default='left')
	products = models.ManyToManyField('Product', blank=True, related_name='collection_rows')
	order = models.PositiveIntegerField(default=0)

	class Meta:
		ordering = ['order']

	def __str__(self):
		return f"{self.collection.title} / Row #{self.order}"


class ZoomCarouselItem(models.Model):
	title = models.CharField(max_length=120, blank=True)
	image = models.ImageField(upload_to='zoom_carousel/')
	link_url = models.URLField(blank=True)
	order = models.PositiveIntegerField(default=0)
	is_active = models.BooleanField(default=True)

	class Meta:
		ordering = ['order']

	def __str__(self):
		return self.title or f"Zoom Item #{self.pk}"


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
	secondary_button_text = models.CharField(max_length=80, blank=True)
	secondary_button_url = models.CharField(max_length=255, blank=True)
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
	shipping_charge = models.DecimalField(
		max_digits=8, decimal_places=2, default=0,
		help_text="Default shipping charge in ₹ (set 0 for free shipping)"
	)
	free_shipping_above = models.DecimalField(
		max_digits=8, decimal_places=2, default=0,
		help_text="Order amount above which shipping is free (0 = always charged)"
	)
	cod_fee = models.DecimalField(
		max_digits=6, decimal_places=2, default=75,
		help_text="Extra fee charged for Cash on Delivery orders"
	)
	return_exchange_fee = models.DecimalField(
		max_digits=6, decimal_places=2, default=100,
		help_text="Fee charged for Return / Exchange requests (₹0 for refunds)"
	)
	razorpay_key_id = models.CharField(
		max_length=200, blank=True,
		help_text="Razorpay Key ID from your Razorpay Dashboard"
	)
	razorpay_key_secret = models.CharField(
		max_length=200, blank=True,
		help_text="Razorpay Key Secret (keep private — never share)"
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


class Coupon(models.Model):
	DISCOUNT_TYPE_CHOICES = [('fixed', 'Fixed Amount (₹)'), ('percent', 'Percentage (%)')]

	code = models.CharField(max_length=50, unique=True)
	description = models.TextField(blank=True)
	discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES, default='percent')
	discount_value = models.DecimalField(max_digits=10, decimal_places=2)
	min_cart_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0,
		help_text="Minimum cart subtotal required")
	max_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
		help_text="Cap for percentage-type discounts (leave blank = no cap)")
	is_active = models.BooleanField(default=True)
	valid_from = models.DateTimeField(null=True, blank=True)
	valid_to = models.DateTimeField(null=True, blank=True)
	usage_limit = models.PositiveIntegerField(null=True, blank=True,
		help_text="Max total uses (blank = unlimited)")
	usage_count = models.PositiveIntegerField(default=0)

	class Meta:
		ordering = ['-id']
		verbose_name = "Coupon"
		verbose_name_plural = "🎟️ Coupons"

	def __str__(self):
		return self.code

	def is_valid(self, cart_total):
		from django.utils import timezone
		from decimal import Decimal
		now = timezone.now()
		if not self.is_active:
			return False, "Coupon is inactive"
		if self.valid_from and now < self.valid_from:
			return False, "Coupon is not yet valid"
		if self.valid_to and now > self.valid_to:
			return False, "Coupon has expired"
		if Decimal(str(cart_total)) < self.min_cart_amount:
			return False, f"Minimum cart amount of ₹{self.min_cart_amount:.0f} required"
		if self.usage_limit and self.usage_count >= self.usage_limit:
			return False, "Coupon usage limit reached"
		return True, "Valid"

	def calculate_discount(self, cart_total):
		from decimal import Decimal
		cart_total = Decimal(str(cart_total))
		if self.discount_type == 'fixed':
			return min(self.discount_value, cart_total)
		discount = (self.discount_value / 100) * cart_total
		if self.max_discount:
			discount = min(discount, self.max_discount)
		return discount


class AdminUserProfile(models.Model):
	"""
	Extended profile for staff/admin users. Stores designation, contact info,
	and a list of feature keys that control which sidebar sections they can access.
	Superusers always have full access regardless of this profile.
	"""
	FEATURE_CHOICES = [
		('dashboard',         'Dashboard & Analytics'),
		('orders',            'Order Management'),
		('products',          'Product Management'),
		('homepage',          'Homepage Management'),
		('marketing',         'Marketing & Trust'),
		('customers',         'Customer Management'),
		('website_frontend',  'Website User-side Functionality'),
	]

	user            = models.OneToOneField(
		settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='admin_profile'
	)
	designation     = models.CharField(max_length=100, blank=True)
	phone_number    = models.CharField(max_length=20, blank=True)
	address         = models.TextField(blank=True)
	assigned_features = models.JSONField(
		default=list,
		help_text='List of feature keys this admin user can access in the dashboard.',
	)
	created_at      = models.DateTimeField(auto_now_add=True)

	class Meta:
		verbose_name          = 'Admin User Profile'
		verbose_name_plural   = '👤 Admin User Profiles'

	def has_feature(self, key):
		return key in (self.assigned_features or [])

	def __str__(self):
		name = self.user.get_full_name() or self.user.username
		return f"{name} — {self.designation or 'Staff'}"


# ──────────────────────────────────────────────────────────
#  RETURN & REFUND MANAGEMENT
# ──────────────────────────────────────────────────────────

class ReturnRequest(models.Model):
	STATUS_CHOICES = [
		('requested',        'Requested'),
		('review',           'Under Review'),
		('approved',         'Approved'),
		('pickup_scheduled', 'Pickup Scheduled'),
		('received',         'Received'),
		('quality_check',    'Quality Check'),
		('refund_pending',   'Refund Pending'),
		('refund_completed', 'Refund Completed'),
		('rejected',         'Rejected'),
	]
	REASON_CHOICES = [
		('damaged',             'Item Damaged'),
		('quality_issue',       'Quality Issue'),
		('size_issue',          'Size / Fit Issue'),
		('wrong_product',       'Wrong Product Received'),
		('customer_preference', 'Customer Changed Mind'),
		('other',               'Other'),
	]
	QC_CHOICES = [
		('pass',        'Pass — Resellable'),
		('fail',        'Fail — Damaged'),
		('investigate', 'Investigate'),
	]
	RESALE_CHOICES = [
		('resellable',    'Resellable'),
		('repair_needed', 'Repair Needed'),
		('damaged',       'Damaged / Scrap'),
	]
	PRIORITY_CHOICES = [
		('low', 'Low'), ('normal', 'Normal'), ('high', 'High'),
	]

	# Core relationships
	order      = models.ForeignKey('Order',     on_delete=models.PROTECT, related_name='return_requests')
	order_item = models.ForeignKey('OrderItem', on_delete=models.SET_NULL, null=True, blank=True, related_name='return_requests')
	customer   = models.ForeignKey(User,        on_delete=models.PROTECT, related_name='return_requests')

	# Product snapshot (denormalised so history is preserved even if product changes)
	product_name = models.CharField(max_length=300)
	product_sku  = models.CharField(max_length=100, blank=True)
	order_amount = models.DecimalField(max_digits=10, decimal_places=2, help_text='Refundable amount cached from order')
	quantity     = models.PositiveIntegerField(default=1)

	RETURN_TYPE_CHOICES = [
		('refund',       'Refund (Money Back)'),
		('exchange',     'Exchange (New Item)'),
		('store_credit', 'Store Credit'),
	]
	CONDITION_CHOICES = [
		('unused_original', 'Unused & Original Packaging'),
		('opened_unused',   'Opened but Unused'),
		('used',            'Used'),
		('damaged',         'Damaged'),
	]
	REFUND_METHOD_CHOICES = [
		('original_payment', 'Original Payment Method'),
		('bank_transfer',    'Bank Transfer'),
	]

	# Return details
	return_reason  = models.CharField(max_length=30, choices=REASON_CHOICES)
	reason_detail  = models.TextField(blank=True)
	return_images  = models.JSONField(default=list, help_text='List of uploaded image URLs/paths')
	return_type    = models.CharField(max_length=15, choices=RETURN_TYPE_CHOICES, default='refund')
	condition      = models.CharField(max_length=20, choices=CONDITION_CHOICES, blank=True)
	pickup_address = models.TextField(blank=True, help_text='Pickup address for return courier')

	# Refund bank details (if bank transfer chosen)
	refund_method         = models.CharField(max_length=20, choices=REFUND_METHOD_CHOICES, default='original_payment')
	account_holder_name   = models.CharField(max_length=200, blank=True)
	account_number        = models.CharField(max_length=50, blank=True)
	ifsc_code             = models.CharField(max_length=20, blank=True)
	bank_name             = models.CharField(max_length=100, blank=True)

	# Processing fee charged to customer (for exchange/return; 0 for refunds)
	processing_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)

	# Status & routing
	status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested')
	priority    = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
	assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_returns')

	# ── Jewellery Quality-Check fields ──────────────────────
	expected_weight      = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True, help_text='grams')
	received_weight      = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True, help_text='grams')
	stone_count_expected = models.PositiveIntegerField(null=True, blank=True)
	stone_count_received = models.PositiveIntegerField(null=True, blank=True)
	hallmark_ok          = models.BooleanField(null=True, blank=True)
	packaging_ok         = models.BooleanField(null=True, blank=True)
	damage_notes         = models.TextField(blank=True)
	qc_result            = models.CharField(max_length=15, choices=QC_CHOICES, blank=True)
	qc_notes             = models.TextField(blank=True)

	# ── Financial ────────────────────────────────────────────
	shipping_deduction  = models.DecimalField(max_digits=8, decimal_places=2, default=0)
	damage_penalty      = models.DecimalField(max_digits=8, decimal_places=2, default=0)
	final_refund_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
	refund_reference    = models.CharField(max_length=200, blank=True, help_text='Payment gateway reference / UTR')

	# ── Recovery ─────────────────────────────────────────────
	resale_status = models.CharField(max_length=15, choices=RESALE_CHOICES, blank=True)
	admin_notes   = models.TextField(blank=True)

	# ── Timestamps ───────────────────────────────────────────
	created_at  = models.DateTimeField(auto_now_add=True)
	updated_at  = models.DateTimeField(auto_now=True)
	approved_at = models.DateTimeField(null=True, blank=True)
	received_at = models.DateTimeField(null=True, blank=True)
	refunded_at = models.DateTimeField(null=True, blank=True)

	class Meta:
		ordering              = ['-created_at']
		verbose_name          = 'Return Request'
		verbose_name_plural   = '↩ Return & Refund Requests'

	def __str__(self):
		return f"RTN-{self.id:04d} | Order #{self.order_id} | {self.product_name}"

	@property
	def rtn_id(self):
		"""
		Generates a premium 8-character return ID with special characters.
		Format: RTN#XXXX  (e.g. RTN#K9AX, RTN#3MQP)
		Deterministic — same ID always produces same RTN number.
		"""
		import hashlib
		# Build a deterministic hash from the DB id
		raw = hashlib.sha256(f"PRINCESS-RTN-{self.id}".encode()).hexdigest().upper()
		# Use full A-Z + 0-9 alphabet via base-36 conversion of first 8 hex digits
		n = int(raw[:8], 16)
		alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # 32 chars, no ambiguous I/O/0/1
		code = ""
		for _ in range(4):
			code = alphabet[n % 32] + code
			n //= 32
		return f"RTN#{code}"

	@property
	def age_days(self):
		from django.utils import timezone as tz
		return (tz.now() - self.created_at).days

	@property
	def is_high_value(self):
		return float(self.order_amount) >= 10000

	@property
	def calculated_refund(self):
		return float(self.order_amount) - float(self.shipping_deduction) - float(self.damage_penalty)


class ReturnStageLog(models.Model):
	"""Immutable audit trail for every stage transition in a return request."""
	return_request = models.ForeignKey(ReturnRequest, on_delete=models.CASCADE, related_name='stage_logs')
	from_status    = models.CharField(max_length=20, blank=True)
	to_status      = models.CharField(max_length=20)
	note           = models.TextField(blank=True)
	changed_by     = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
	changed_at     = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['changed_at']
		verbose_name = 'Return Stage Log'

	def __str__(self):
		return f"RTN-{self.return_request_id:04d}: {self.from_status} → {self.to_status}"
