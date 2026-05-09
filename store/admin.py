from django.contrib import admin
from django.core.exceptions import ValidationError
from django.contrib import messages as admin_messages
from .models import (
	Category, Product, ProductImage, Order, OrderItem,
	NewsletterSubscriber, ContactMessage, Announcement, HomepageSectionProduct,
	Collection, CollectionRow, ZoomCarouselItem, HeroSlide, SiteSettings,
)
from .forms import CollectionForm, CollectionRowForm, ZoomCarouselItemForm
class OrderItemInline(admin.TabularInline):
	model = OrderItem
	extra = 0
	readonly_fields = ('product', 'quantity', 'price')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
	list_display = ('id', 'user', 'status', 'created_at', 'total', 'mobile_number')
	list_filter = ('status', 'created_at', 'user')
	search_fields = ('id', 'user__username', 'shipping_address', 'shipping_city', 'shipping_postal_code', 'shipping_country')
	inlines = [OrderItemInline]
	actions = ['mark_as_processing', 'mark_as_shipped', 'mark_as_delivered', 'mark_as_cancelled']

	def mark_as_processing(self, request, queryset):
		queryset.update(status='processing')
	mark_as_processing.short_description = "Mark selected orders as Processing"

	def mark_as_shipped(self, request, queryset):
		queryset.update(status='shipped')
	mark_as_shipped.short_description = "Mark selected orders as Shipped"

	def mark_as_delivered(self, request, queryset):
		queryset.update(status='delivered')
	mark_as_delivered.short_description = "Mark selected orders as Delivered"

	def mark_as_cancelled(self, request, queryset):
		queryset.update(status='cancelled')
	mark_as_cancelled.short_description = "Mark selected orders as Cancelled"

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
	list_display = ('order', 'product', 'quantity', 'price')
	search_fields = ('order__id', 'product__name')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
	list_display = ('name',)

# Inline for Product Additional Images
class ProductImageInline(admin.TabularInline):
	model = ProductImage
	extra = 1
	max_num = 3  # Main image + 3 additional = 4 total
	fields = ('image',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
	list_display = ('name', 'category', 'price', 'stock', 'is_active', 'created_at')
	list_filter = ('category', 'is_active', 'created_at')
	search_fields = ('name', 'description')
	list_editable = ('is_active',)
	inlines = [ProductImageInline]
	actions = ['activate_products', 'deactivate_products']
	
	def activate_products(self, request, queryset):
		queryset.update(is_active=True)
	activate_products.short_description = "Activate selected products"
	
	def deactivate_products(self, request, queryset):
		queryset.update(is_active=False)
	deactivate_products.short_description = "Deactivate selected products"

# Newsletter Subscribers Admin
@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
	list_display = ('email', 'subscribed_at', 'is_active')
	list_filter = ('subscribed_at', 'is_active')
	search_fields = ('email',)
	actions = ['activate_subscribers', 'deactivate_subscribers']

	def activate_subscribers(self, request, queryset):
		queryset.update(is_active=True)
	activate_subscribers.short_description = "Activate selected subscribers"

	def deactivate_subscribers(self, request, queryset):
		queryset.update(is_active=False)
	deactivate_subscribers.short_description = "Deactivate selected subscribers"

# Contact Messages Admin
@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
	list_display = ('name', 'email', 'created_at', 'is_read', 'is_replied')
	list_filter = ('created_at', 'is_read', 'is_replied')
	search_fields = ('name', 'email', 'message')
	actions = ['mark_as_read', 'mark_as_unread', 'mark_as_replied']

	def mark_as_read(self, request, queryset):
		queryset.update(is_read=True)
	mark_as_read.short_description = "Mark selected messages as read"

	def mark_as_unread(self, request, queryset):
		queryset.update(is_read=False)
	mark_as_unread.short_description = "Mark selected messages as unread"

	def mark_as_replied(self, request, queryset):
		queryset.update(is_replied=True)
	mark_as_replied.short_description = "Mark selected messages as replied"


# ============================================================================
# HOMEPAGE MANAGEMENT SECTION
# ============================================================================

# Announcement Admin
@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
	list_display = ('title', 'message_preview', 'is_active', 'created_at', 'updated_at')
	list_filter = ('is_active', 'created_at')
	search_fields = ('title', 'message')
	list_editable = ('is_active',)
	actions = ['activate_announcements', 'deactivate_announcements']
	fieldsets = (
		('Announcement Content', {
			'fields': ('title', 'message')
		}),
		('Display Settings', {
			'fields': ('is_active',),
			'description': 'Control whether this announcement appears on the website'
		}),
	)
	
	def message_preview(self, obj):
		return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
	message_preview.short_description = 'Message Preview'
	
	def activate_announcements(self, request, queryset):
		count = queryset.update(is_active=True)
		self.message_user(request, f'{count} announcement(s) activated successfully.')
	activate_announcements.short_description = "✓ Activate selected announcements"
	
	def deactivate_announcements(self, request, queryset):
		count = queryset.update(is_active=False)
		self.message_user(request, f'{count} announcement(s) deactivated successfully.')
	deactivate_announcements.short_description = "✗ Deactivate selected announcements"


# Custom Admin for Homepage Product Sections
class HomepageSectionProductAdmin(admin.ModelAdmin):
	list_display = ('get_section_display', 'position', 'get_product_info', 'product_stock', 'created_at')
	list_filter = ('section_type',)
	search_fields = ('product__name',)
	ordering = ('section_type', 'position')
	list_per_page = 20
	
	fieldsets = (
		('Section Configuration', {
			'fields': ('section_type', 'position'),
			'description': 'Select the homepage section and position (1-4). Maximum 4 products per section.'
		}),
		('Product Selection', {
			'fields': ('product',),
			'description': 'Choose the product to display in this section'
		}),
	)
	
	def get_section_display(self, obj):
		colors = {
			'most_selling': '🔥',
			'trending': '📈',
			'new_launch': '✨',
			'featured': '⭐'
		}
		icon = colors.get(obj.section_type, '')
		return f"{icon} {obj.get_section_type_display()}"
	get_section_display.short_description = 'Section'
	
	def get_product_info(self, obj):
		return f"{obj.product.name} (₹{obj.product.price})"
	get_product_info.short_description = 'Product'
	
	def product_stock(self, obj):
		if obj.product.stock > 10:
			return f"✓ {obj.product.stock} in stock"
		elif obj.product.stock > 0:
			return f"⚠ {obj.product.stock} in stock"
		else:
			return "✗ Out of stock"
	product_stock.short_description = 'Stock Status'
	
	def get_form(self, request, obj=None, **kwargs):
		form = super().get_form(request, obj, **kwargs)
		# Add help text to the form
		if 'position' in form.base_fields:
			form.base_fields['position'].help_text = 'Position in section (1-4). Each section can have maximum 4 products.'
		if 'product' in form.base_fields:
			# Only show active products in dropdown
			form.base_fields['product'].queryset = form.base_fields['product'].queryset.filter(is_active=True)
		return form
	
	def save_model(self, request, obj, form, change):
		try:
			obj.full_clean()  # This will call the clean() method in the model
			super().save_model(request, obj, form, change)
			admin_messages.success(request, f'✓ Product "{obj.product.name}" added to {obj.get_section_type_display()} at position {obj.position}')
		except ValidationError as e:
			error_msg = str(e.message_dict) if hasattr(e, 'message_dict') else str(e)
			admin_messages.error(request, f'✗ Error: {error_msg}')
			raise


# Custom Admin Site Configuration for Homepage Sections
class MostSellingProductAdmin(HomepageSectionProductAdmin):
	def get_queryset(self, request):
		return super().get_queryset(request).filter(section_type='most_selling')
	
	def formfield_for_choice_field(self, db_field, request, **kwargs):
		if db_field.name == 'section_type':
			kwargs['initial'] = 'most_selling'
			kwargs['widget'] = admin.widgets.AdminTextInputWidget(attrs={'readonly': 'readonly'})
		return super().formfield_for_choice_field(db_field, request, **kwargs)


class TrendingProductAdmin(HomepageSectionProductAdmin):
	def get_queryset(self, request):
		return super().get_queryset(request).filter(section_type='trending')
	
	def formfield_for_choice_field(self, db_field, request, **kwargs):
		if db_field.name == 'section_type':
			kwargs['initial'] = 'trending'
			kwargs['widget'] = admin.widgets.AdminTextInputWidget(attrs={'readonly': 'readonly'})
		return super().formfield_for_choice_field(db_field, request, **kwargs)


class NewLaunchProductAdmin(HomepageSectionProductAdmin):
	def get_queryset(self, request):
		return super().get_queryset(request).filter(section_type='new_launch')
	
	def formfield_for_choice_field(self, db_field, request, **kwargs):
		if db_field.name == 'section_type':
			kwargs['initial'] = 'new_launch'
			kwargs['widget'] = admin.widgets.AdminTextInputWidget(attrs={'readonly': 'readonly'})
		return super().formfield_for_choice_field(db_field, request, **kwargs)


class FeaturedProductAdmin(HomepageSectionProductAdmin):
	def get_queryset(self, request):
		return super().get_queryset(request).filter(section_type='featured')
	
	def formfield_for_choice_field(self, db_field, request, **kwargs):
		if db_field.name == 'section_type':
			kwargs['initial'] = 'featured'
			kwargs['widget'] = admin.widgets.AdminTextInputWidget(attrs={'readonly': 'readonly'})
		return super().formfield_for_choice_field(db_field, request, **kwargs)


# Register the main model with a general admin
admin.site.register(HomepageSectionProduct, HomepageSectionProductAdmin)


# ============================================================================
# COLLECTIONS MANAGEMENT
# ============================================================================

class CollectionRowInline(admin.TabularInline):
	model = CollectionRow
	extra = 1
	fields = ('title', 'image', 'image_position', 'order')
	ordering = ('order',)


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
	form = CollectionForm
	list_display = ('title', 'slug', 'is_active', 'num_rows', 'order', 'created_at')
	list_filter = ('is_active', 'created_at')
	search_fields = ('title', 'slug')
	prepopulated_fields = {'slug': ('title',)}
	list_editable = ('is_active', 'order')
	inlines = [CollectionRowInline]
	ordering = ('order', '-created_at')
	
	fieldsets = (
		('Basic Information', {
			'fields': ('title', 'slug', 'order'),
			'description': 'Collection name and URL slug'
		}),
		('Display Settings', {
			'fields': ('is_active',),
		}),
	)
	
	def num_rows(self, obj):
		count = obj.rows.count()
		return f"📌 {count} row{'s' if count != 1 else ''}"
	num_rows.short_description = 'Rows'
	
	def save_model(self, request, obj, form, change):
		super().save_model(request, obj, form, change)
		action = "updated" if change else "created"
		admin_messages.success(request, f'✓ Collection "{obj.title}" {action} successfully')


@admin.register(CollectionRow)
class CollectionRowAdmin(admin.ModelAdmin):
	form = CollectionRowForm
	list_display = ('collection', 'title_or_order', 'image_position', 'num_products', 'order')
	list_filter = ('collection', 'image_position')
	search_fields = ('collection__title', 'title')
	ordering = ('collection', 'order')
	filter_horizontal = ('products',)
	
	fieldsets = (
		('Collection & Layout', {
			'fields': ('collection', 'image_position', 'order'),
			'description': 'Select which collection this row belongs to and where the image appears'
		}),
		('Image & Overlay', {
			'fields': ('image', 'title'),
			'description': 'Row image and optional overlay text'
		}),
		('Products', {
			'fields': ('products',),
			'description': 'Select products to display in the carousel (up to 12 will be shown, scrollable)',
			'classes': ('wide',)
		}),
	)
	
	def title_or_order(self, obj):
		return obj.title or f"Row #{obj.order}"
	title_or_order.short_description = 'Title / Order'
	
	def num_products(self, obj):
		count = obj.products.count()
		return f"📦 {count}"
	num_products.short_description = 'Products'
	
	def save_model(self, request, obj, form, change):
		super().save_model(request, obj, form, change)
		action = "updated" if change else "created"
		admin_messages.success(request, f'✓ Collection row {action} successfully')


# ============================================================================
# ZOOM CAROUSEL MANAGEMENT
# ============================================================================

@admin.register(ZoomCarouselItem)
class ZoomCarouselItemAdmin(admin.ModelAdmin):
	form = ZoomCarouselItemForm
	list_display = ('title_or_order', 'image_preview', 'is_active', 'order', 'has_link')
	list_filter = ('is_active', 'order')
	search_fields = ('title', 'link_url')
	list_editable = ('is_active', 'order')
	ordering = ('order',)
	
	fieldsets = (
		('Item Information', {
			'fields': ('title', 'order'),
			'description': 'Title is optional; order defines position in carousel'
		}),
		('Image', {
			'fields': ('image',),
			'description': 'Square image recommended (will be displayed in 3D carousel)'
		}),
		('Link Settings', {
			'fields': ('link_url',),
			'description': 'URL to collection, product, or external link (optional)'
		}),
		('Display', {
			'fields': ('is_active',),
		}),
	)
	
	def title_or_order(self, obj):
		return obj.title or f"Item #{obj.pk}"
	title_or_order.short_description = 'Title'
	
	def image_preview(self, obj):
		if obj.image:
			return f"✓ Uploaded"
		return "✗ No image"
	image_preview.short_description = 'Image'
	
	def has_link(self, obj):
		if obj.link_url:
			return "🔗 Yes"
		return "—"
	has_link.short_description = 'Link'
	
	def save_model(self, request, obj, form, change):
		super().save_model(request, obj, form, change)
		action = "updated" if change else "created"
		admin_messages.success(request, f'✓ Carousel item {action} successfully')


# ============================================================================
# HERO SLIDES & SITE SETTINGS
# ============================================================================

@admin.register(HeroSlide)
class HeroSlideAdmin(admin.ModelAdmin):
	list_display = ('__str__', 'order', 'is_active', 'created_at')
	list_editable = ('order', 'is_active')
	ordering = ('order',)
	fieldsets = (
		('Slide Background', {
			'fields': ('background_image', 'background_video'),
			'description': 'Provide either an image or a video as slide background.',
		}),
		('Content', {
			'fields': ('heading', 'subheading', 'button_text', 'button_url'),
		}),
		('Display Settings', {
			'fields': ('order', 'is_active'),
		}),
	)


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
	list_display = ('__str__', 'glass_flash_enabled')

	def has_add_permission(self, request):
		return not SiteSettings.objects.exists()

	def has_delete_permission(self, request, obj=None):
		return False
