
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from .models import (
	UserProfile, Address, Order, OrderItem, Product, Category, Cart, CartItem,
	Announcement, HomepageSectionProduct, InstagramReel, TrustBadge, WishlistItem, ProductReview,
	HomepageSectionContent, OrderLifecycleLog, EditorialMedia,
	Collection, CollectionRow, ZoomCarouselItem, HeroSlide, SiteSettings, Coupon,
	UserNotification,
	ReturnRequest, ReturnStageLog,
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


# Checkout: order success
@login_required
def order_success_view(request, order_id):
	order = get_object_or_404(Order, pk=order_id, user=request.user)
	return render(request, 'store/order_success.html', {'order': order})

from django.db.models import Q
from django import forms
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone

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
	is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
	if is_ajax:
		item_count = sum(i.quantity for i in cart.items.all())
		return JsonResponse({'ok': True, 'item_count': item_count})
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
	related_products = Product.objects.filter(
		category=product.category, is_active=True
	).prefetch_related('additional_images', 'videos').exclude(pk=pk)[:4]
	in_wishlist = False
	if request.user.is_authenticated:
		in_wishlist = WishlistItem.objects.filter(user=request.user, product=product).exists()

	# Use direct rating fields on the product (set by admin)
	average_rating = float(product.rating)
	total_ratings = product.rating_count
	full_stars = int(average_rating)
	half_star = (average_rating - full_stars) >= 0.5
	empty_stars = 5 - full_stars - (1 if half_star else 0)

	# Keep approved reviews for the reviews section below the fold
	approved_reviews = product.reviews.filter(is_approved=True)

	# Build gallery images (main + up to 3 additional)
	gallery_images = []
	if product.image:
		gallery_images.append(product.image.url)
	gallery_images += [img.image.url for img in product.additional_images.all()[:3]]

	return render(request, 'store/product_detail.html', {
		'product': product,
		'related_products': related_products,
		'in_wishlist': in_wishlist,
		'product_videos': product.videos.all(),
		'approved_reviews': approved_reviews,
		'total_ratings': total_ratings,
		'average_rating': average_rating,
		'full_stars': range(full_stars),
		'half_star': half_star,
		'empty_stars': range(empty_stars),
		'gallery_images': gallery_images,
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
		
		# Get homepage section products (no hard limit — slider handles >4)
		most_selling = Product.objects.filter(
			homepage_sections__section_type='most_selling',
			homepage_sections__is_active=True,
			is_active=True
		).prefetch_related('additional_images', 'videos').distinct().order_by('homepage_sections__position')

		trending_products = Product.objects.filter(
			homepage_sections__section_type='trending',
			homepage_sections__is_active=True,
			is_active=True
		).prefetch_related('additional_images', 'videos').distinct().order_by('homepage_sections__position')

		new_launch = Product.objects.filter(
			homepage_sections__section_type='new_launch',
			homepage_sections__is_active=True,
			is_active=True
		).prefetch_related('additional_images', 'videos').distinct().order_by('homepage_sections__position')

		featured_products = Product.objects.filter(
			homepage_sections__section_type='featured',
			homepage_sections__is_active=True,
			is_active=True
		).prefetch_related('additional_images', 'videos').distinct().order_by('homepage_sections__position')
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
		collection_rows = CollectionRow.objects.select_related('collection').prefetch_related('products').filter(collection__is_active=True).order_by('order')
		zoom_carousel_items = ZoomCarouselItem.objects.filter(is_active=True).order_by('order')
		hero_slides = HeroSlide.objects.filter(is_active=True).order_by('order')
		glass_flash_enabled = SiteSettings.get_settings().glass_flash_enabled

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
			'collection_rows': collection_rows,
			'zoom_carousel_items': zoom_carousel_items,
			'hero_content': section_content.get('hero'),
			'launch_featured_media': section_content.get('launch_featured_media'),
			'exquisite_content': section_content.get('exquisite_collection'),
			'account_cards_media': section_content.get('account_cards_media'),
			'reels_content': section_content.get('instagram_reels'),
			'hero_slides': hero_slides,
			'glass_flash_enabled': glass_flash_enabled,
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


def collections_list_view(request):
	collections = Collection.objects.filter(is_active=True).order_by('order', 'title')
	return render(request, 'store/collections_list.html', {'collections': collections})


def collection_detail_view(request, slug):
	collection = get_object_or_404(Collection, slug=slug, is_active=True)
	rows = collection.rows.prefetch_related('products').order_by('order')
	products = Product.objects.filter(collection_rows__collection=collection, is_active=True).distinct().prefetch_related('additional_images', 'videos')
	return render(request, 'store/collection_detail.html', {
		'collection': collection,
		'rows': rows,
		'products': products,
	})

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
	profile, _ = UserProfile.objects.get_or_create(user=user)
	addresses = Address.objects.filter(user=user)
	if request.method == 'POST':
		for field in ('first_name', 'last_name', 'email', 'mobile', 'gender', 'occupation'):
			val = request.POST.get(field, '').strip()
			if val is not None:
				setattr(profile, field, val)
		for date_field in ('birthdate', 'anniversary', 'spouse_birthday', 'kids_birthday'):
			val = request.POST.get(date_field, '').strip()
			setattr(profile, date_field, val if val else None)
		profile.save()
		messages.success(request, 'Profile updated!')
		return redirect('profile')
	return render(request, 'store/profile.html', {
		'user': user,
		'profile': profile,
		'addresses': addresses,
	})

@login_required
def order_history_view(request):
	from datetime import timedelta, date as _date
	status_filter = request.GET.get('tab', 'all')
	qs = Order.objects.filter(user=request.user).prefetch_related(
		'items__product', 'items__review', 'return_requests'
	).order_by('-created_at')
	if status_filter == 'active':
		qs = qs.filter(status__in=['pending', 'processing', 'packed', 'shipped', 'out_for_delivery'])
	elif status_filter == 'delivered':
		qs = qs.filter(status='delivered')
	elif status_filter == 'cancelled':
		qs = qs.filter(status__in=['cancelled', 'returned', 'rto'])

	DELIVERY_DAYS = {'pending': 7, 'processing': 5, 'packed': 4, 'shipped': 3, 'out_for_delivery': 1}
	orders_data = []
	for order in qs:
		conf = f"AJ{order.created_at.year}{order.id:05d}"
		if order.status == 'delivered' and order.delivered_at:
			exp_delivery = order.delivered_at
		else:
			days = DELIVERY_DAYS.get(order.status, 7)
			exp_delivery = order.created_at + timedelta(days=days)
		can_cancel = order.status in ('pending', 'processing', 'packed')
		can_return = (order.status == 'delivered' and order.delivered_at and
		              (timezone.now() - order.delivered_at).days <= 7)
		reviewable_ids = set()
		if order.status == 'delivered':
			for item in order.items.all():
				if not hasattr(item, 'review'):
					reviewable_ids.add(item.id)

		# ── Return progress for mini strip ──────────────────────────
		RTN_PHASE_MAP = {
			'requested': 1, 'review': 2,
			'approved': 3, 'pickup_scheduled': 3,
			'received': 4, 'quality_check': 4, 'refund_pending': 4,
			'refund_completed': 5,
			'rejected': -1,
		}
		all_rtns = list(order.return_requests.all())   # uses prefetch cache
		rtn_obj = next(
			(r for r in sorted(all_rtns, key=lambda r: r.created_at, reverse=True)
			 if r.status != 'rejected'),
			None
		) or (sorted(all_rtns, key=lambda r: r.created_at, reverse=True)[0] if all_rtns else None)
		has_return = bool(rtn_obj)
		rtn_phase  = RTN_PHASE_MAP.get(rtn_obj.status, 1) if rtn_obj else 0

		orders_data.append({
			'order': order,
			'conf': conf,
			'exp_delivery': exp_delivery,
			'can_cancel': can_cancel,
			'can_return': can_return,
			'reviewable_ids': reviewable_ids,
			'has_return': has_return,
			'rtn_phase': rtn_phase,
		})

	return render(request, 'store/order_history.html', {
		'orders_data': orders_data,
		'tab': status_filter,
	})


@login_required
def order_timeline_api(request, order_id):
	order = get_object_or_404(Order, pk=order_id, user=request.user)
	from datetime import timedelta
	# STATUS_RANK lets us mark earlier steps as "done" even when admin jumped
	# (e.g. set "shipped" without first setting "packed")
	STATUS_RANK = {
		'pending': 0, 'processing': 0,
		'packed': 1, 'shipped': 2, 'out_for_delivery': 3, 'delivered': 4,
	}
	cur_rank = STATUS_RANK.get(order.status, 0)

	# If order is in a return/refund state, all delivery steps count as done
	is_return_status = order.status in ('returned', 'refund_pending', 'refund_completed', 'rto')

	def _is_done(key, ts, key_rank):
		if is_return_status:
			return True
		return bool(ts) or (cur_rank >= key_rank)

	steps = [
		{'key': 'ordered',          'label': 'Order Placed',     'icon': '🛍️',
		 'date': order.created_at,
		 'done': True,                                                          'rank': 0},
		{'key': 'packed',           'label': 'Packed',           'icon': '📦',
		 'date': order.packed_at,
		 'done': _is_done('packed', order.packed_at, 1),                        'rank': 1},
		{'key': 'shipped',          'label': 'Shipped',          'icon': '🚚',
		 'date': order.shipped_at,
		 'done': _is_done('shipped', order.shipped_at, 2),                      'rank': 2},
		{'key': 'out_for_delivery', 'label': 'Out for Delivery', 'icon': '📬',
		 'date': order.out_for_delivery_at,
		 'done': _is_done('out_for_delivery', order.out_for_delivery_at, 3),    'rank': 3},
		{'key': 'delivered',        'label': 'Delivered',        'icon': '✅',
		 'date': order.delivered_at,
		 'done': _is_done('delivered', order.delivered_at, 4),                  'rank': 4},
	]
	OFFSETS = {'packed': 1, 'shipped': 3, 'out_for_delivery': 5, 'delivered': 7}
	for s in steps:
		raw_date = s.get('date')
		if s['done'] and raw_date:
			s['date_fmt'] = raw_date.strftime('%b %d, %Y')
		elif s['done']:
			s['date_fmt'] = 'Completed'
		else:
			s['est'] = (order.created_at + timedelta(days=OFFSETS.get(s['key'], 1))).strftime('%b %d')

	# ── Return / Refund stages ───────────────────────────────────────────────
	return_steps = []
	has_return = False
	try:
		# Get the most recent return request (prefer non-rejected)
		rtn = (
			order.return_requests.exclude(status='rejected').order_by('-created_at').first()
			or order.return_requests.order_by('-created_at').first()
		)
		if rtn:
			has_return = True
			RTN_RANK = {
				'requested': 1, 'review': 2,
				'approved': 3, 'pickup_scheduled': 4,
				'received': 5, 'quality_check': 5,
				'refund_pending': 6,
				'refund_completed': 7,
				'rejected': 7,
			}
			rr = RTN_RANK.get(rtn.status, 1)
			is_rejected = (rtn.status == 'rejected')

			def _rd(key_rank, ts=None):
				return bool(ts) or (rr >= key_rank)

			return_steps = [
				{'key': 'rtn_requested',  'label': 'Return Requested',
				 'icon': '↩️', 'date': rtn.created_at,
				 'done': True,             'is_return': True},
				{'key': 'rtn_review',     'label': 'Under Review',
				 'icon': '🔍', 'date': None,
				 'done': _rd(2),           'is_return': True},
				{'key': 'rtn_approved',   'label': 'Return Approved',
				 'icon': '✅', 'date': rtn.approved_at,
				 'done': _rd(3, rtn.approved_at), 'is_return': True},
				{'key': 'rtn_pickup',     'label': 'Pickup & Quality Check',
				 'icon': '🚚', 'date': rtn.received_at,
				 'done': _rd(5, rtn.received_at), 'is_return': True},
				{'key': 'rtn_processing', 'label': 'Refund Processing',
				 'icon': '💳', 'date': None,
				 'done': _rd(6),           'is_return': True},
			]
			# Final step — completed or rejected
			if is_rejected:
				return_steps.append({
					'key': 'rtn_rejected', 'label': 'Return Rejected',
					'icon': '❌', 'date': rtn.updated_at,
					'done': True, 'is_return': True, 'is_rejected': True,
				})
			else:
				return_steps.append({
					'key': 'rtn_completed', 'label': 'Refund Completed',
					'icon': '🎉', 'date': rtn.refunded_at,
					'done': _rd(7, rtn.refunded_at), 'is_return': True,
				})

			# Format dates on return steps; add estimated dates for pending stages
			RTN_EST_OFFSETS = {
				'rtn_review': 2, 'rtn_approved': 4,
				'rtn_pickup': 7, 'rtn_processing': 9, 'rtn_completed': 14,
			}
			for s in return_steps:
				raw_date = s.get('date')
				if s['done'] and raw_date:
					s['date_fmt'] = raw_date.strftime('%b %d, %Y')
				elif s['done']:
					s['date_fmt'] = 'In Progress'
				else:
					offset = RTN_EST_OFFSETS.get(s['key'])
					if offset is not None:
						s['est'] = (rtn.created_at + timedelta(days=offset)).strftime('%b %d')
					s['date_fmt'] = None
	except Exception:
		pass

	all_steps = steps + return_steps
	done_count = sum(1 for s in all_steps if s['done'])
	total      = max(len(all_steps), 1)
	# Smooth 0–100% based on fraction of all steps done
	if total == 1:
		progress_pct = 100 if all_steps[0]['done'] else 0
	else:
		progress_pct = int((done_count - 1) / (total - 1) * 100) if done_count > 0 else 0

	items = [{'name': i.product.name,
	          'image': i.product.image.url if i.product.image else '',
	          'qty': i.quantity,
	          'price': float(i.price)} for i in order.items.select_related('product')]
	return JsonResponse({
		'ok': True,
		'order_id': order.id,
		'conf': f"AJ{order.created_at.year}{order.id:05d}",
		'status': order.get_status_display(),
		'status_key': order.status,
		'steps': all_steps,
		'progress_pct': progress_pct,
		'has_return': has_return,
		'items': items,
	})


@login_required
def cancel_order_api(request, order_id):
	if request.method != 'POST':
		return JsonResponse({'ok': False, 'error': 'POST required'}, status=405)
	order = get_object_or_404(Order, pk=order_id, user=request.user)
	if order.status not in ('pending', 'processing', 'packed'):
		return JsonResponse({'ok': False, 'error': 'Order cannot be cancelled at this stage.'}, status=400)
	order.status = 'cancelled'
	order.save(update_fields=['status', 'updated_at'])
	# Restore stock
	for item in order.items.select_related('product'):
		item.product.stock += item.quantity
		item.product.save(update_fields=['stock'])
	return JsonResponse({'ok': True})


@login_required
def buy_again_api(request, order_id):
	if request.method != 'POST':
		return JsonResponse({'ok': False, 'error': 'POST required'}, status=405)
	order = get_object_or_404(Order, pk=order_id, user=request.user)
	cart, _ = Cart.objects.get_or_create(user=request.user)
	added = 0
	for item in order.items.select_related('product'):
		if item.product.is_active and item.product.stock > 0:
			cart_item, created = CartItem.objects.get_or_create(cart=cart, product=item.product)
			if not created:
				cart_item.quantity += item.quantity
			else:
				cart_item.quantity = item.quantity
			cart_item.save()
			added += 1
	if added == 0:
		return JsonResponse({'ok': False, 'error': 'No items available to add to cart.'}, status=400)
	return JsonResponse({'ok': True, 'added': added})

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


# ─── Cart JSON API ────────────────────────────────────────────────────────────

def _cart_summary(cart, coupon_code=None):
	"""Build the full cart payload dict for the slide-in panel."""
	from decimal import Decimal
	items = cart.items.select_related('product').prefetch_related('product__additional_images')
	settings_obj = SiteSettings.objects.first()
	shipping_charge = Decimal(str(settings_obj.shipping_charge)) if settings_obj else Decimal('0')
	free_shipping_above = Decimal(str(settings_obj.free_shipping_above)) if settings_obj else Decimal('0')

	items_data = []
	mrp_total = Decimal('0')
	price_total = Decimal('0')
	for item in items:
		p = item.product
		mrp = Decimal(str(p.mrp)) if p.mrp else Decimal(str(p.price))
		price = Decimal(str(p.price))
		img_url = p.image.url if p.image else ''
		items_data.append({
			'id': item.id,
			'product_id': p.id,
			'name': p.name,
			'image': img_url,
			'price': float(price),
			'mrp': float(mrp),
			'quantity': item.quantity,
			'subtotal': float(price * item.quantity),
		})
		mrp_total += mrp * item.quantity
		price_total += price * item.quantity

	discount_on_mrp = mrp_total - price_total

	coupon_discount = Decimal('0')
	coupon_error = None
	coupon_obj = None
	if coupon_code:
		try:
			coupon_obj = Coupon.objects.get(code__iexact=coupon_code)
			valid, msg = coupon_obj.is_valid(price_total)
			if valid:
				coupon_discount = coupon_obj.calculate_discount(price_total)
			else:
				coupon_error = msg
				coupon_obj = None
		except Coupon.DoesNotExist:
			coupon_error = 'Invalid coupon code'

	subtotal_after_coupon = price_total - coupon_discount
	shipping = Decimal('0')
	if subtotal_after_coupon > 0:
		if free_shipping_above > 0 and subtotal_after_coupon >= free_shipping_above:
			shipping = Decimal('0')
		else:
			shipping = shipping_charge

	estimated_total = subtotal_after_coupon + shipping

	return {
		'items': items_data,
		'summary': {
			'mrp_total': float(mrp_total),
			'discount_on_mrp': float(discount_on_mrp),
			'price_total': float(price_total),
			'coupon_discount': float(coupon_discount),
			'shipping': float(shipping),
			'free_shipping_above': float(free_shipping_above),
			'estimated_total': float(estimated_total),
		},
		'coupon_code': coupon_obj.code if coupon_obj else None,
		'coupon_error': coupon_error,
		'item_count': sum(i['quantity'] for i in items_data),
	}


@login_required
def cart_data_api(request):
	cart, _ = Cart.objects.get_or_create(user=request.user)
	coupon_code = request.GET.get('coupon') or request.session.get('applied_coupon')
	data = _cart_summary(cart, coupon_code)
	return JsonResponse({'ok': True, **data})


@login_required
def cart_update_api(request):
	if request.method != 'POST':
		return JsonResponse({'ok': False, 'error': 'POST required'}, status=405)
	try:
		body = json.loads(request.body)
	except Exception:
		return JsonResponse({'ok': False, 'error': 'Invalid JSON'}, status=400)
	item_id = body.get('item_id')
	quantity = body.get('quantity', 1)
	cart = get_object_or_404(Cart, user=request.user)
	item = get_object_or_404(CartItem, pk=item_id, cart=cart)
	try:
		quantity = int(quantity)
	except (ValueError, TypeError):
		return JsonResponse({'ok': False, 'error': 'Invalid quantity'}, status=400)
	if quantity <= 0:
		item.delete()
	else:
		item.quantity = quantity
		item.save()
	data = _cart_summary(cart, request.session.get('applied_coupon'))
	return JsonResponse({'ok': True, **data})


@login_required
def cart_remove_api(request):
	if request.method != 'POST':
		return JsonResponse({'ok': False, 'error': 'POST required'}, status=405)
	try:
		body = json.loads(request.body)
	except Exception:
		return JsonResponse({'ok': False, 'error': 'Invalid JSON'}, status=400)
	item_id = body.get('item_id')
	cart = get_object_or_404(Cart, user=request.user)
	item = get_object_or_404(CartItem, pk=item_id, cart=cart)
	item.delete()
	data = _cart_summary(cart, request.session.get('applied_coupon'))
	return JsonResponse({'ok': True, **data})


@login_required
def apply_coupon_api(request):
	if request.method != 'POST':
		return JsonResponse({'ok': False, 'error': 'POST required'}, status=405)
	try:
		body = json.loads(request.body)
	except Exception:
		return JsonResponse({'ok': False, 'error': 'Invalid JSON'}, status=400)
	coupon_code = body.get('coupon_code', '').strip()
	if coupon_code:
		request.session['applied_coupon'] = coupon_code
	else:
		request.session.pop('applied_coupon', None)
	cart, _ = Cart.objects.get_or_create(user=request.user)
	data = _cart_summary(cart, coupon_code)
	return JsonResponse({'ok': True, **data})


@login_required
def recommended_products_api(request):
	cart, _ = Cart.objects.get_or_create(user=request.user)
	cart_product_ids = list(cart.items.values_list('product_id', flat=True))
	recs = Product.objects.filter(is_active=True).exclude(id__in=cart_product_ids).order_by('-rating', '-created_at')[:6]
	data = []
	for p in recs:
		data.append({
			'id': p.id,
			'name': p.name,
			'price': float(p.price),
			'mrp': float(p.mrp) if p.mrp else float(p.price),
			'image': p.image.url if p.image else '',
			'rating': float(p.rating) if p.rating else 0,
			'url': f'/store/products/{p.id}/',
		})
	return JsonResponse({'ok': True, 'products': data})


# ─── Address API ──────────────────────────────────────────────────────────────

def _address_to_dict(a):
	return {
		'id': a.id, 'full_name': a.full_name,
		'address_line1': a.address_line1, 'address_line2': a.address_line2,
		'city': a.city, 'state': a.state, 'postal_code': a.postal_code,
		'country': a.country, 'mobile': a.mobile, 'is_default': a.is_default,
	}


@login_required
def addresses_api(request):
	if request.method == 'GET':
		addrs = Address.objects.filter(user=request.user)
		return JsonResponse({'ok': True, 'addresses': [_address_to_dict(a) for a in addrs]})
	try:
		data = json.loads(request.body)
		is_first = not Address.objects.filter(user=request.user).exists()
		addr = Address.objects.create(
			user=request.user,
			full_name=data['full_name'],
			address_line1=data['address_line1'],
			address_line2=data.get('address_line2', ''),
			city=data['city'],
			state=data['state'],
			postal_code=data['postal_code'],
			country=data.get('country', 'India'),
			mobile=data['mobile'],
			is_default=data.get('is_default', is_first),
		)
		return JsonResponse({'ok': True, 'address': _address_to_dict(addr)})
	except Exception as e:
		return JsonResponse({'ok': False, 'error': str(e)}, status=400)


@login_required
def address_update_api(request, addr_id):
	addr = get_object_or_404(Address, pk=addr_id, user=request.user)
	try:
		data = json.loads(request.body)
		for field in ('full_name', 'address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country', 'mobile'):
			if field in data:
				setattr(addr, field, data[field])
		if data.get('is_default'):
			addr.is_default = True
		addr.save()
		return JsonResponse({'ok': True, 'address': _address_to_dict(addr)})
	except Exception as e:
		return JsonResponse({'ok': False, 'error': str(e)}, status=400)


@login_required
def address_delete_api(request, addr_id):
	addr = get_object_or_404(Address, pk=addr_id, user=request.user)
	was_default = addr.is_default
	addr.delete()
	if was_default:
		first = Address.objects.filter(user=request.user).first()
		if first:
			first.is_default = True
			first.save()
	return JsonResponse({'ok': True})


@login_required
def address_set_default_api(request, addr_id):
	addr = get_object_or_404(Address, pk=addr_id, user=request.user)
	Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
	addr.is_default = True
	addr.save()
	return JsonResponse({'ok': True})


# ─── Place Order (COD) ────────────────────────────────────────────────────────

def _create_order_from_cart(user, address, payment_method, coupon_code=None,
                             razorpay_order_id='', razorpay_payment_id=''):
	from decimal import Decimal
	cart, _ = Cart.objects.get_or_create(user=user)
	items = cart.items.select_related('product')
	if not items.exists():
		raise ValueError('Cart is empty')
	settings_obj = SiteSettings.get_settings()
	price_total = sum(Decimal(str(item.product.price)) * item.quantity for item in items)
	coupon_discount = Decimal('0')
	if coupon_code:
		try:
			coupon = Coupon.objects.get(code__iexact=coupon_code)
			valid, _ = coupon.is_valid(price_total)
			if valid:
				coupon_discount = coupon.calculate_discount(price_total)
				coupon.usage_count += 1
				coupon.save()
		except Coupon.DoesNotExist:
			pass
	subtotal = price_total - coupon_discount
	free_above = Decimal(str(settings_obj.free_shipping_above))
	ship = Decimal(str(settings_obj.shipping_charge))
	shipping = Decimal('0') if (free_above > 0 and subtotal >= free_above) else ship
	cod_fee = Decimal(str(settings_obj.cod_fee)) if payment_method == 'cod' else Decimal('0')
	total = subtotal + shipping + cod_fee
	order = Order.objects.create(
		user=user,
		shipping_name=address.full_name,
		shipping_address=f"{address.address_line1} {address.address_line2}".strip(),
		shipping_city=address.city,
		shipping_state=address.state,
		shipping_postal_code=address.postal_code,
		shipping_country=address.country,
		mobile_number=address.mobile,
		total=total,
		payment_method=payment_method,
		payment_status='paid' if payment_method != 'cod' else 'pending',
		razorpay_order_id=razorpay_order_id,
		razorpay_payment_id=razorpay_payment_id,
		coupon_discount=coupon_discount,
		shipping_amount=shipping,
		cod_fee_amount=cod_fee,
	)
	for item in items:
		OrderItem.objects.create(order=order, product=item.product, quantity=item.quantity, price=item.product.price)
		item.product.stock = max(0, item.product.stock - item.quantity)
		item.product.save()
	items.delete()
	return order


@login_required
def order_confirmation_view(request, order_id):
	from datetime import timedelta
	order = get_object_or_404(Order, pk=order_id, user=request.user)
	# Build the 5-step fulfillment timeline
	timeline = [
		{'key': 'ordered',          'label': 'Ordered',          'icon': '🛍️', 'date': order.created_at,          'completed': True},
		{'key': 'packed',           'label': 'Packed',           'icon': '📦', 'date': order.packed_at,            'completed': bool(order.packed_at)},
		{'key': 'shipped',          'label': 'Shipped',          'icon': '🚚', 'date': order.shipped_at,           'completed': bool(order.shipped_at)},
		{'key': 'out_for_delivery', 'label': 'Out for Delivery', 'icon': '📬', 'date': order.out_for_delivery_at,  'completed': bool(order.out_for_delivery_at)},
		{'key': 'delivered',        'label': 'Delivered',        'icon': '✅', 'date': order.delivered_at,         'completed': bool(order.delivered_at)},
	]
	# Add estimated dates for future steps (relative to order placement)
	offsets = {'packed': 1, 'shipped': 3, 'out_for_delivery': 5, 'delivered': 7}
	for step in timeline:
		if not step['completed']:
			step['estimated'] = order.created_at + timedelta(days=offsets.get(step['key'], 1))
	# Determine which step is currently "active" (latest completed)
	active_idx = 0
	for i, step in enumerate(timeline):
		if step['completed']:
			active_idx = i
	for i, step in enumerate(timeline):
		step['is_active'] = (i == active_idx)
	# Payment breakdown
	items = order.items.select_related('product')
	price_total = sum(item.price * item.quantity for item in items)
	is_online = order.payment_method != 'cod'
	return render(request, 'store/order_confirmation.html', {
		'order': order,
		'timeline': timeline,
		'items': items,
		'price_total': price_total,
		'is_online': is_online,
	})


@login_required
def place_order_api(request):
	if request.method != 'POST':
		return JsonResponse({'ok': False, 'error': 'POST required'}, status=405)
	try:
		data = json.loads(request.body)
	except Exception:
		return JsonResponse({'ok': False, 'error': 'Invalid JSON'}, status=400)
	addr_id = data.get('address_id')
	payment_method = data.get('payment_method', 'cod')
	coupon_code = data.get('coupon_code', '') or request.session.get('applied_coupon', '')
	if payment_method not in ('cod',):
		return JsonResponse({'ok': False, 'error': 'Use Razorpay endpoint for online payments'}, status=400)
	if not addr_id:
		return JsonResponse({'ok': False, 'error': 'Please select a delivery address.'}, status=400)
	try:
		address = Address.objects.get(pk=addr_id, user=request.user)
	except Address.DoesNotExist:
		return JsonResponse({'ok': False, 'error': 'Selected address not found. Please choose another.'}, status=400)
	try:
		order = _create_order_from_cart(request.user, address, 'cod', coupon_code)
		request.session.pop('applied_coupon', None)
		return JsonResponse({'ok': True, 'order_id': order.id})
	except Exception as e:
		return JsonResponse({'ok': False, 'error': str(e)}, status=400)


# ─── Razorpay ─────────────────────────────────────────────────────────────────

@login_required
def create_razorpay_order_api(request):
	if request.method != 'POST':
		return JsonResponse({'ok': False, 'error': 'POST required'}, status=405)
	try:
		data = json.loads(request.body)
	except Exception:
		return JsonResponse({'ok': False, 'error': 'Invalid JSON'}, status=400)
	from decimal import Decimal
	try:
		import razorpay
	except ImportError:
		return JsonResponse({'ok': False, 'error': 'Online payments not available right now. Please use Cash on Delivery.'}, status=503)
	settings_obj = SiteSettings.get_settings()
	if not settings_obj.razorpay_key_id or not settings_obj.razorpay_key_secret:
		return JsonResponse({'ok': False, 'error': 'Razorpay not configured. Contact admin.'}, status=503)
	addr_id = data.get('address_id')
	payment_method = data.get('payment_method', 'upi')
	coupon_code = data.get('coupon_code', '') or request.session.get('applied_coupon', '')
	if not addr_id:
		return JsonResponse({'ok': False, 'error': 'Please select a delivery address.'}, status=400)
	try:
		address = Address.objects.get(pk=addr_id, user=request.user)
	except Address.DoesNotExist:
		return JsonResponse({'ok': False, 'error': 'Selected address not found.'}, status=400)
	try:
		cart = Cart.objects.get_or_create(user=request.user)[0]
		items = cart.items.select_related('product')
		price_total = sum(Decimal(str(i.product.price)) * i.quantity for i in items)
		coupon_discount = Decimal('0')
		if coupon_code:
			try:
				coupon = Coupon.objects.get(code__iexact=coupon_code)
				valid, _ = coupon.is_valid(price_total)
				if valid:
					coupon_discount = coupon.calculate_discount(price_total)
			except Coupon.DoesNotExist:
				pass
		subtotal = price_total - coupon_discount
		free_above = Decimal(str(settings_obj.free_shipping_above))
		ship = Decimal(str(settings_obj.shipping_charge))
		shipping = Decimal('0') if (free_above > 0 and subtotal >= free_above) else ship
		total_paise = int((subtotal + shipping) * 100)
		client = razorpay.Client(auth=(settings_obj.razorpay_key_id, settings_obj.razorpay_key_secret))
		from django.utils import timezone
		rz_order = client.order.create({
			'amount': total_paise,
			'currency': 'INR',
			'receipt': f'order_{request.user.id}_{int(timezone.now().timestamp())}',
		})
		request.session['pending_checkout'] = {
			'address_id': addr_id,
			'payment_method': payment_method,
			'coupon_code': coupon_code,
			'razorpay_order_id': rz_order['id'],
		}
		profile, _ = UserProfile.objects.get_or_create(user=request.user)
		return JsonResponse({
			'ok': True,
			'razorpay_order_id': rz_order['id'],
			'amount': total_paise,
			'key': settings_obj.razorpay_key_id,
			'name': request.user.get_full_name() or request.user.username,
			'email': profile.email or request.user.email,
			'mobile': profile.mobile or '',
		})
	except Exception as e:
		return JsonResponse({'ok': False, 'error': str(e)}, status=400)


@login_required
def verify_payment_api(request):
	if request.method != 'POST':
		return JsonResponse({'ok': False, 'error': 'POST required'}, status=405)
	try:
		data = json.loads(request.body)
	except Exception:
		return JsonResponse({'ok': False, 'error': 'Invalid JSON'}, status=400)
	try:
		import razorpay
	except ImportError:
		return JsonResponse({'ok': False, 'error': 'Payment module not available.'}, status=503)
	settings_obj = SiteSettings.get_settings()
	client = razorpay.Client(auth=(settings_obj.razorpay_key_id, settings_obj.razorpay_key_secret))
	try:
		client.utility.verify_payment_signature({
			'razorpay_order_id': data['razorpay_order_id'],
			'razorpay_payment_id': data['razorpay_payment_id'],
			'razorpay_signature': data['razorpay_signature'],
		})
	except Exception:
		return JsonResponse({'ok': False, 'error': 'Payment verification failed'}, status=400)
	pending = request.session.get('pending_checkout', {})
	try:
		address = get_object_or_404(Address, pk=pending.get('address_id'), user=request.user)
		order = _create_order_from_cart(
			request.user, address,
			pending.get('payment_method', 'upi'),
			pending.get('coupon_code', ''),
			razorpay_order_id=data['razorpay_order_id'],
			razorpay_payment_id=data['razorpay_payment_id'],
		)
		request.session.pop('pending_checkout', None)
		request.session.pop('applied_coupon', None)
		return JsonResponse({'ok': True, 'order_id': order.id})
	except Exception as e:
		return JsonResponse({'ok': False, 'error': str(e)}, status=400)


# ── Mobile Menu: Categories with preview images ──────────────────────────────
def categories_with_previews_api(request):
	"""Returns active categories each with one preview product image.
	Used by the mobile menu 2-column category grid."""
	categories = Category.objects.filter(is_active=True).order_by('name')
	data = []
	for cat in categories:
		preview = (
			Product.objects
			.filter(category=cat, is_active=True)
			.exclude(image='')
			.only('id', 'image')
			.first()
		)
		data.append({
			'id': cat.id,
			'name': cat.name,
			'url': f'/store/category/{cat.id}/',
			'preview_image': preview.image.url if preview and preview.image else None,
		})
	return JsonResponse(data, safe=False)


# ─── User Notification APIs ──────────────────────────────────────────────────

@login_required
def user_notifications_api(request):
    """Return the current user's notifications with unread count."""
    notifs = UserNotification.objects.filter(user=request.user)[:30]
    unread_count = UserNotification.objects.filter(user=request.user, is_read=False).count()
    data = []
    for n in notifs:
        data.append({
            "id": n.id,
            "title": n.title,
            "message": n.message,
            "notif_type": n.notif_type,
            "is_read": n.is_read,
            "order_id": n.related_order_id,
            "time": n.created_at.strftime("%b %d, %H:%M"),
        })
    return JsonResponse({"success": True, "notifications": data, "unread_count": unread_count})


@login_required
def user_mark_notification_read_api(request, notif_id):
    """Mark a single notification as read."""
    if request.method == "POST":
        notif = get_object_or_404(UserNotification, id=notif_id, user=request.user)
        notif.is_read = True
        notif.save(update_fields=["is_read"])
        return JsonResponse({"success": True})
    return JsonResponse({"success": False}, status=405)


@login_required
def user_mark_all_notifications_read_api(request):
    """Mark all notifications as read for current user."""
    if request.method == "POST":
        UserNotification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return JsonResponse({"success": True})
    return JsonResponse({"success": False}, status=405)


# ══════════════════════════════════════════════════════════════
#  USER-SIDE RETURN & REFUND PAGE
# ══════════════════════════════════════════════════════════════

def returns_page_view(request):
    """Render the luxury returns & refund page."""
    settings_obj = SiteSettings.get_settings()
    return render(request, 'store/return_request.html', {
        'return_exchange_fee': float(settings_obj.return_exchange_fee),
    })


def returns_lookup_order_api(request):
    """Find an order by order_id + email (or mobile) — allows guest access."""
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "POST required"}, status=405)
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    order_id = str(data.get("order_id", "")).strip()
    email    = (data.get("email", "") or "").strip().lower()
    mobile   = (data.get("mobile", "") or "").strip()

    if not order_id:
        return JsonResponse({"success": False, "error": "Order ID is required."}, status=400)

    try:
        qs = Order.objects.filter(id=int(order_id))
        if request.user.is_authenticated:
            # Logged-in users can look up their own orders directly — no extra verification
            qs = qs.filter(user=request.user)
        elif email:
            qs = qs.filter(user__email__iexact=email)
        elif mobile:
            qs = qs.filter(mobile_number=mobile)
        else:
            return JsonResponse({"success": False, "error": "Please provide email or mobile."}, status=400)
        order = qs.get()
    except (Order.DoesNotExist, ValueError):
        return JsonResponse({"success": False, "error": "No order found with these details. Please check and try again."}, status=404)

    # Only delivered orders are eligible
    if order.status not in ("delivered", "returned", "rto"):
        return JsonResponse({
            "success": False,
            "error": f"This order is currently '{order.get_status_display()}'. Returns can only be raised for delivered orders.",
        }, status=400)

    # Check if a return already exists and isn't rejected
    existing = ReturnRequest.objects.filter(order=order).exclude(status="rejected").first()
    if existing:
        return JsonResponse({
            "success": False,
            "error": f"A return request ({existing.rtn_id}) already exists for this order with status '{existing.get_status_display()}'.",
        }, status=400)

    # Build items list
    items = []
    for it in order.items.select_related('product').all():
        try:
            img = it.product.image.url if it.product.image else ''
        except Exception:
            img = ''
        items.append({
            "item_id":  it.id,
            "product":  it.product.name,
            "sku":      getattr(it.product, 'sku', ''),
            "image":    img,
            "price":    float(it.price),
            "quantity": it.quantity,
        })

    try:
        address_parts = [
            order.shipping_name or order.user.get_full_name(),
            order.shipping_address,
            order.shipping_city,
            order.shipping_state,
            order.shipping_postal_code,
        ]
        address_str = "\n".join(
            p for p in address_parts
            if p and p not in ('Address not provided', 'City not provided', 'State not provided', '00000')
        )
    except Exception:
        address_str = getattr(order, 'shipping_address', '') or ''

    try:
        total_val = float(order.total)
    except Exception:
        total_val = 0.0

    return JsonResponse({
        "success": True,
        "order": {
            "id":           order.id,
            "status":       order.status,
            "total":        total_val,
            "created_at":   order.created_at.strftime("%d %B %Y"),
            "delivered_at": order.delivered_at.strftime("%d %B %Y") if order.delivered_at else "N/A",
            "items":        items,
            "address":      address_str,
        },
    })


def returns_submit_api(request):
    """Submit a return / exchange / refund request (login required)."""
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "error": "Please log in to submit a return."}, status=401)
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "POST required"}, status=405)

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    order_id   = data.get("order_id")
    item_id    = data.get("item_id")   # optional
    reason     = (data.get("reason") or "").strip()
    detail     = (data.get("detail") or "").strip()
    return_type = (data.get("return_type") or "refund").strip()
    condition   = (data.get("condition") or "").strip()
    refund_method = (data.get("refund_method") or "original_payment").strip()
    pickup_address = (data.get("pickup_address") or "").strip()
    images      = data.get("images", [])
    # Bank details (if bank transfer)
    account_holder_name = (data.get("account_holder_name") or "").strip()
    account_number      = (data.get("account_number") or "").strip()
    ifsc_code           = (data.get("ifsc_code") or "").strip()
    bank_name           = (data.get("bank_name") or "").strip()

    if not order_id or not reason:
        return JsonResponse({"success": False, "error": "Order ID and reason are required."}, status=400)

    try:
        order = Order.objects.get(id=int(order_id), user=request.user)
    except (Order.DoesNotExist, ValueError):
        return JsonResponse({"success": False, "error": "Order not found."}, status=404)

    if order.status not in ("delivered", "returned", "rto"):
        return JsonResponse({"success": False, "error": "Order is not eligible for return."}, status=400)

    existing = ReturnRequest.objects.filter(order=order).exclude(status="rejected").first()
    if existing:
        return JsonResponse({"success": False, "error": f"A return ({existing.rtn_id}) already exists for this order."}, status=400)

    # Determine processing fee
    settings_obj = SiteSettings.get_settings()
    fee = float(settings_obj.return_exchange_fee) if return_type == 'exchange' else 0.0

    # Resolve order item
    order_item = None
    product_name = order.items.first().product.name if order.items.exists() else 'N/A'
    product_sku  = ''
    order_amount = float(order.total)
    if item_id:
        try:
            oi = order.items.get(id=int(item_id))
            order_item   = oi
            product_name = oi.product.name
            product_sku  = getattr(oi.product, 'sku', '')
            order_amount = float(oi.price) * oi.quantity
        except OrderItem.DoesNotExist:
            pass

    rr = ReturnRequest.objects.create(
        order=order,
        order_item=order_item,
        customer=request.user,
        product_name=product_name,
        product_sku=product_sku,
        order_amount=order_amount,
        quantity=order_item.quantity if order_item else 1,
        return_reason=reason,
        reason_detail=detail,
        return_images=images,
        return_type=return_type,
        condition=condition,
        refund_method=refund_method,
        pickup_address=pickup_address,
        account_holder_name=account_holder_name,
        account_number=account_number,
        ifsc_code=ifsc_code,
        bank_name=bank_name,
        processing_fee=fee,
        status='requested',
        priority='high' if order_amount >= 10000 else 'normal',
    )
    # Initial log entry
    ReturnStageLog.objects.create(
        return_request=rr,
        from_status='',
        to_status='requested',
        note=f"Return request submitted by customer. Type: {return_type}. Reason: {reason}.",
        changed_by=request.user,
    )
    # Notify customer
    UserNotification.objects.create(
        user=request.user,
        title=f"Return Request Submitted — {rr.rtn_id}",
        message=f"Your {return_type} request for Order #{order.id} has been received. Reference: {rr.rtn_id}. We will review within 24–48 hours.",
        notif_type="order_updated",
        related_order=order,
    )

    return JsonResponse({
        "success": True,
        "rtn_id": rr.rtn_id,
        "message": "Your return request has been submitted. We'll review it within 24–48 hours.",
    })


@login_required
def returns_my_requests_api(request):
    """Return all return requests for the logged-in user."""
    rrs = ReturnRequest.objects.filter(customer=request.user).order_by('-created_at')
    data = []
    for rr in rrs:
        data.append({
            "id":          rr.id,
            "rtn_id":      rr.rtn_id,
            "order_id":    rr.order_id,
            "product":     rr.product_name,
            "return_type": rr.return_type,
            "status":      rr.status,
            "created_at":  rr.created_at.strftime("%d %b %Y"),
            "amount":      float(rr.order_amount),
            "timeline":    [
                {
                    "stage":     lg.to_status,
                    "note":      lg.note,
                    "date":      lg.changed_at.strftime("%d %b %Y, %H:%M"),
                }
                for lg in rr.stage_logs.all()
            ],
        })
    return JsonResponse({"success": True, "requests": data})
