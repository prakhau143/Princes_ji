
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from .models import (
	UserProfile, Order, OrderItem, Product, Category, Cart, CartItem,
	Announcement, HomepageSectionProduct, InstagramReel, TrustBadge, WishlistItem, ProductReview,
	HomepageSectionContent, OrderLifecycleLog, EditorialMedia,
)
from django import forms

# Order detail view
@login_required
def order_detail_view(request, order_id):
	order = get_object_or_404(Order, pk=order_id, user=request.user)
	return render(request, 'store/order_detail.html', {'order': order})

# Shipping form for checkout
class ShippingForm(forms.Form):
	address = forms.CharField(
		max_length=255, 
		widget=forms.TextInput(attrs={
			'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-pink-500 transition-all',
			'placeholder': '123 Main Street'
		})
	)
	city = forms.CharField(
		max_length=100, 
		widget=forms.TextInput(attrs={
			'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-pink-500 transition-all',
			'placeholder': 'New York'
		})
	)
	state = forms.CharField(
		max_length=100,
		widget=forms.TextInput(attrs={
			'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-pink-500 transition-all',
			'placeholder': 'Rajasthan'
		})
	)
	postal_code = forms.CharField(
		max_length=20, 
		widget=forms.TextInput(attrs={
			'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-pink-500 transition-all',
			'placeholder': '10001'
		})
	)
	country = forms.CharField(
		max_length=100, 
		widget=forms.TextInput(attrs={
			'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-pink-500 transition-all',
			'placeholder': 'United States'
		})
	)
	mobile_number = forms.CharField(
		max_length=20, 
		widget=forms.TextInput(attrs={
			'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-pink-500 transition-all',
			'placeholder': '+1 (555) 123-4567'
		})
	)


# Checkout: collect shipping details
@login_required
def checkout_view(request):
	cart, _ = Cart.objects.get_or_create(user=request.user)
	items = cart.items.select_related('product')
	total = sum(item.product.price * item.quantity for item in items)
	if not items.exists():
		messages.error(request, "Your cart is empty.")
		return redirect('cart')
	if request.method == 'POST':
		form = ShippingForm(request.POST)
		if form.is_valid():
			# Save shipping info in session and go to review
			request.session['shipping'] = form.cleaned_data
			return redirect('checkout_review')
	else:
		form = ShippingForm()
	return render(request, 'store/checkout.html', {'form': form, 'items': items, 'total': total})

# Checkout: review order
@login_required
def checkout_review_view(request):
	cart, _ = Cart.objects.get_or_create(user=request.user)
	items = cart.items.select_related('product')
	shipping = request.session.get('shipping')
	if not shipping or not items.exists():
		return redirect('checkout')
	total = sum(item.product.price * item.quantity for item in items)
	stock_errors = []
	for item in items:
		if item.quantity > item.product.stock:
			stock_errors.append(f"Not enough stock for {item.product.name} (Available: {item.product.stock}, In cart: {item.quantity})")
	if request.method == 'POST':
		if stock_errors:
			for err in stock_errors:
				messages.error(request, err)
			return redirect('checkout_review')
		# Create order and order items
		order = Order.objects.create(
			user=request.user,
			shipping_address=shipping['address'],
			shipping_city=shipping['city'],
			shipping_state=shipping['state'],
			shipping_postal_code=shipping['postal_code'],
			shipping_country=shipping['country'],
			mobile_number=shipping['mobile_number'],
			total=total
		)
		for item in items:
			OrderItem.objects.create(
				order=order,
				product=item.product,
				quantity=item.quantity,
				price=item.product.price
			)
			# Deduct stock
			item.product.stock -= item.quantity
			item.product.save()
		# Clear cart
		items.delete()
		messages.success(request, "Order placed successfully!")
		# Optionally clear shipping info
		request.session.pop('shipping', None)
		return redirect('order_success', order_id=order.id)
	return render(request, 'store/checkout_review.html', {'items': items, 'shipping': shipping, 'total': total, 'stock_errors': stock_errors})

# Checkout: order success
@login_required
def order_success_view(request, order_id):
	order = get_object_or_404(Order, pk=order_id, user=request.user)
	return render(request, 'store/order_success.html', {'order': order})

from django.db.models import Q
from django import forms
from django.contrib import messages
from django.core.paginator import Paginator

# Cart views

@login_required
def cart_view(request):
	cart, _ = Cart.objects.get_or_create(user=request.user)
	items = cart.items.select_related('product')
	if request.method == 'POST':
		for item in items:
			quantity_str = request.POST.get(f'quantity_{item.id}')
			if quantity_str is not None:
				try:
					quantity = int(quantity_str)
					if quantity > 0:
						item.quantity = quantity
						item.save()
					else:
						item.delete()
				except ValueError:
					pass
		return redirect('cart')
	total = sum(item.product.price * item.quantity for item in items)
	return render(request, 'store/cart.html', {'cart': cart, 'items': items, 'total': total})


# Optional: Separate view for updating a single cart item quantity (AJAX or form action)
@login_required
def update_cart_item_quantity(request, item_id):
	cart = get_object_or_404(Cart, user=request.user)
	item = get_object_or_404(CartItem, pk=item_id, cart=cart)
	if request.method == 'POST':
		quantity_str = request.POST.get('quantity')
		try:
			quantity = int(quantity_str)
			if quantity > 0:
				item.quantity = quantity
				item.save()
			else:
				item.delete()
		except (ValueError, TypeError):
			pass
	return redirect('cart')

@login_required
def add_to_cart_view(request, product_id):
	product = get_object_or_404(Product, pk=product_id)
	cart, _ = Cart.objects.get_or_create(user=request.user)
	item, created = CartItem.objects.get_or_create(cart=cart, product=product)
	if not created:
		item.quantity += 1
		item.save()
	# If 'buynow' param is present, go directly to checkout
	if request.GET.get('buynow') == '1':
		return redirect('checkout')
	return redirect('cart')

@login_required
def remove_from_cart_view(request, item_id):
	cart = get_object_or_404(Cart, user=request.user)
	item = get_object_or_404(CartItem, pk=item_id, cart=cart)
	item.delete()
	return redirect('cart')

# List products by category
@login_required
def category_products_view(request, category_id):
	category = get_object_or_404(Category, pk=category_id, is_active=True)
	products = Product.objects.filter(category=category).prefetch_related('additional_images')
	categories = Category.objects.filter(is_active=True)
	wishlist_product_ids = set(
		WishlistItem.objects.filter(user=request.user).values_list('product_id', flat=True)
	)
	return render(request, 'store/product_list.html', {
		'products': products,
		'categories': categories,
		'selected_category': str(category_id),
		'search_query': '',
		'category_obj': category,
		'wishlist_product_ids': wishlist_product_ids,
	})

def product_detail_view(request, pk):
	product = get_object_or_404(Product, pk=pk)
	# Get related products from the same category, excluding the current product
	related_products = Product.objects.filter(
		category=product.category,
		stock__gt=0
	).prefetch_related('additional_images', 'videos').exclude(pk=pk)[:4]
	in_wishlist = False
	if request.user.is_authenticated:
		in_wishlist = WishlistItem.objects.filter(user=request.user, product=product).exists()
	
	return render(request, 'store/product_detail.html', {
		'product': product,
		'related_products': related_products,
		'in_wishlist': in_wishlist,
		'product_videos': product.videos.all(),
	})


@login_required
def toggle_wishlist_view(request, product_id):
	if request.method != 'POST':
		return JsonResponse({'success': False, 'error': 'Invalid request method'})
	product = get_object_or_404(Product, pk=product_id)
	obj = WishlistItem.objects.filter(user=request.user, product=product)
	if obj.exists():
		obj.delete()
		return JsonResponse({'success': True, 'in_wishlist': False})
	WishlistItem.objects.create(user=request.user, product=product)
	return JsonResponse({'success': True, 'in_wishlist': True})


@login_required
def wishlist_view(request):
	items = WishlistItem.objects.filter(user=request.user).select_related('product').order_by('-created_at')
	owners_fav = list(Product.objects.filter(
		homepage_sections__section_type='owners_fav',
		homepage_sections__is_active=True,
		is_active=True,
	).order_by('homepage_sections__position').distinct())
	return render(request, 'store/wishlist.html', {'items': items, 'owners_fav': owners_fav})


@login_required
def add_order_item_review_view(request, order_id, item_id):
	if request.method != 'POST':
		return redirect('order_detail', order_id=order_id)
	order = get_object_or_404(Order, pk=order_id, user=request.user)
	item = get_object_or_404(OrderItem, pk=item_id, order=order)
	if order.status != 'delivered':
		messages.error(request, 'Review is allowed only after delivery.')
		return redirect('order_detail', order_id=order_id)
	if hasattr(item, 'review'):
		messages.error(request, 'You already reviewed this product for this order.')
		return redirect('order_detail', order_id=order_id)
	try:
		rating = int(request.POST.get('rating') or 0)
	except ValueError:
		rating = 0
	title = (request.POST.get('title') or '').strip()
	body = (request.POST.get('body') or '').strip()
	reviewer_name = (request.POST.get('reviewer_name') or '').strip()
	if rating < 1 or rating > 5:
		messages.error(request, 'Please select a valid rating (1-5).')
		return redirect('order_detail', order_id=order_id)
	review = ProductReview.objects.create(
		product=item.product,
		user=request.user,
		order_item=item,
		rating=rating,
		title=title,
		body=body,
		reviewer_name=reviewer_name,
		is_approved=False,
		is_visible=False,
	)
	if request.FILES.get('reviewer_image'):
		review.reviewer_image = request.FILES['reviewer_image']
		review.save(update_fields=['reviewer_image'])
	messages.success(request, 'Review submitted successfully.')
	return redirect('order_detail', order_id=order_id)

@login_required
def product_list_view(request):
	query = request.GET.get('q', '')
	category_id = request.GET.get('category', '')
	products = Product.objects.all().prefetch_related('additional_images', 'videos').order_by('-id')
	categories = Category.objects.filter(is_active=True)
	wishlist_product_ids = set(
		WishlistItem.objects.filter(user=request.user).values_list('product_id', flat=True)
	)
	if query:
		products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))
	if category_id:
		products = products.filter(category_id=category_id)
	return render(request, 'store/product_list.html', {
		'products': products,
		'categories': categories,
		'selected_category': category_id,
		'search_query': query,
		'wishlist_product_ids': wishlist_product_ids,
	})
from django import forms
from django.contrib import messages

# Create your views here.

def home_view(request):
		# Get active announcements
		announcements = Announcement.objects.filter(is_active=True)
		section_content = {
			item.section_key: item
			for item in HomepageSectionContent.objects.filter(is_active=True)
		}
		
		# Get homepage section products
		most_selling = Product.objects.filter(
			homepage_sections__section_type='most_selling',
			homepage_sections__is_active=True,
			is_active=True
		).prefetch_related('additional_images', 'videos').distinct().order_by('homepage_sections__position')[:4]
		
		trending_products = Product.objects.filter(
			homepage_sections__section_type='trending',
			homepage_sections__is_active=True,
			is_active=True
		).prefetch_related('additional_images', 'videos').distinct().order_by('homepage_sections__position')[:4]
		
		new_launch = Product.objects.filter(
			homepage_sections__section_type='new_launch',
			homepage_sections__is_active=True,
			is_active=True
		).prefetch_related('additional_images', 'videos').distinct().order_by('homepage_sections__position')[:4]
		
		featured_products = Product.objects.filter(
			homepage_sections__section_type='featured',
			homepage_sections__is_active=True,
			is_active=True
		).prefetch_related('additional_images', 'videos').distinct().order_by('homepage_sections__position')[:4]
		exquisite_products = Product.objects.filter(
			homepage_sections__section_type='exquisite',
			homepage_sections__is_active=True,
			is_active=True
		).prefetch_related('additional_images', 'videos').distinct().order_by('homepage_sections__position')[:12]
		
		# Fallback: If no products in sections, show recent active products
		if not trending_products.exists():
			trending_products = Product.objects.filter(stock__gt=0, is_active=True)[:4]
		
		top_picks = exquisite_products if exquisite_products.exists() else Product.objects.filter(stock__gt=0, is_active=True).prefetch_related('additional_images', 'videos').order_by('-created_at')[:12]
		active_reels = InstagramReel.objects.filter(is_active=True).order_by('sort_order', '-created_at')[:8]
		trust_badges = TrustBadge.objects.filter(is_active=True).order_by('sort_order', 'id')[:8]
		approved_reviews = ProductReview.objects.filter(is_approved=True, is_visible=True).select_related('product', 'user').order_by('-created_at')[:12]
		editorial_items = EditorialMedia.objects.filter(is_active=True).select_related('product').order_by('order', 'created_at')

		context = {
			'announcements': announcements,
			'most_selling': most_selling,
			'trending_products': trending_products,
			'new_launch': new_launch,
			'featured_products': featured_products,
			'top_picks': top_picks,
			'active_reels': active_reels,
			'trust_badges': trust_badges,
			'approved_reviews': approved_reviews,
			'editorial_items': editorial_items,
			'hero_content': section_content.get('hero'),
			'launch_featured_media': section_content.get('launch_featured_media'),
			'exquisite_content': section_content.get('exquisite_collection'),
			'account_cards_media': section_content.get('account_cards_media'),
			'reels_content': section_content.get('instagram_reels'),
		}
		
		if request.user.is_authenticated:
			# Get cart and order count for dashboard
			cart, _ = Cart.objects.get_or_create(user=request.user)
			cart_items = cart.items.select_related('product')
			cart_total = sum(item.product.price * item.quantity for item in cart_items)
			order_count = Order.objects.filter(user=request.user).count()
			wishlist_count = WishlistItem.objects.filter(user=request.user).count()
			wishlist_product_ids = set(
				WishlistItem.objects.filter(user=request.user).values_list('product_id', flat=True)
			)
			context.update({
				'dashboard': True,
				'cart_items': cart_items,
				'cart_total': cart_total,
				'order_count': order_count,
				'wishlist_count': wishlist_count,
				'wishlist_product_ids': wishlist_product_ids,
			})
		else:
			context['dashboard'] = False
		
		return render(request, 'store/home.html', context)

# Note: Authentication views have been moved to store/auth_views.py
# These old functions are kept for reference but are no longer used
# All authentication is now handled through the main ecommerce/urls.py


# Form for editing user profile
class UserProfileForm(forms.ModelForm):
	class Meta:
		model = UserProfile
		fields = ['address', 'phone', 'mobile']

@login_required
def profile_view(request):
	user = request.user
	# Get or create user profile
	profile, created = UserProfile.objects.get_or_create(user=user)
	# Get or create cart and items
	cart, _ = Cart.objects.get_or_create(user=user)
	cart_items = cart.items.select_related('product')
	cart_total = sum(item.product.price * item.quantity for item in cart_items)
	if request.method == 'POST':
		form = UserProfileForm(request.POST, instance=profile)
		if form.is_valid():
			form.save()
			messages.success(request, 'Profile updated!')
			return redirect('profile')
	else:
		form = UserProfileForm(instance=profile)
	return render(request, 'store/profile.html', {
		'user': user,
		'form': form,
		'profile': profile,
		'cart_items': cart_items,
		'cart_total': cart_total,
	})

@login_required
def order_history_view(request):
	orders = Order.objects.filter(user=request.user).prefetch_related('items__product').order_by('-created_at')
	reviewable_item_ids = set()
	for order in orders:
		if order.status == 'delivered':
			for item in order.items.all():
				if not hasattr(item, 'review'):
					reviewable_item_ids.add(item.id)
	return render(request, 'store/order_history.html', {
		'orders': orders,
		'reviewable_item_ids': reviewable_item_ids,
	})

@login_required
def order_detail_view(request, order_id):
	order = get_object_or_404(Order, pk=order_id, user=request.user)
	items = order.items.select_related('product').all()
	reviewable_item_ids = set()
	if order.status == 'delivered':
		for item in items:
			if not hasattr(item, 'review'):
				reviewable_item_ids.add(item.id)
	return render(request, 'store/order_detail.html', {
		'order': order,
		'reviewable_item_ids': reviewable_item_ids,
	})

@login_required
def contact_view(request):
	if request.method == 'POST':
		name = request.POST.get('name')
		email = request.POST.get('email')
		subject = request.POST.get('subject', 'General Inquiry')
		message = request.POST.get('message')
		
		if name and email and message:
			from .models import ContactMessage
			try:
				ContactMessage.objects.create(
					name=name,
					email=email,
					subject=subject,
					message=message
				)
				from django.contrib import messages
				messages.success(request, 'Thank you for your message! We will get back to you soon.')
			except Exception as e:
				from django.contrib import messages
				messages.error(request, 'There was an error sending your message. Please try again.')
			return redirect('contact')
	
	return render(request, 'store/contact.html', {
		'phone': '+91 9876543210',
		'email': 'princess.jewellery015@gmail.com'
	})

@login_required
def size_guide_view(request):
	return render(request, 'store/size_guide.html')

@login_required
def care_instructions_view(request):
	return render(request, 'store/care_instructions.html')

def newsletter_subscribe_view(request):
	if request.method == 'POST':
		email = request.POST.get('email')
		name = request.POST.get('name', '')

		if email:
			from .models import NewsletterSubscriber
			try:
				NewsletterSubscriber.objects.create(
					email=email,
					name=name,
					source='Website'
				)
				from django.contrib import messages
				messages.success(request, 'Thank you for subscribing to our newsletter! You will receive exclusive offers and updates.')
			except:
				from django.contrib import messages
				messages.error(request, 'You are already subscribed to our newsletter.')

	return redirect('home')

@login_required
def shipping_returns_view(request):
	return render(request, 'store/shipping_returns.html')
