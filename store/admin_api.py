from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404
from django.db.models import Q, Sum, Count, F, ExpressionWrapper, DecimalField
from django.db.models.functions import TruncDate, TruncMonth
import json
from .models import (
    CustomerProfile,
    Order,
    OrderItem,
    Product,
    Category,
    User,
    Notification,
    UserNotification,
    InstagramReel,
    TrustBadge,
    MarketingSpend,
    ExpenseEntry,
    ProductReview,
    Announcement,
    WishlistItem,
    HomepageSectionProduct,
    HomepageSectionContent,
    ProductImage,
    ProductVideo,
    ProductVariant,
    OrderLifecycleLog,
    EditorialMedia,
	Collection,
	CollectionRow,
	ZoomCarouselItem,
	HeroSlide,
	SiteSettings,
	Coupon,
	AdminUserProfile,
	ReturnRequest,
	ReturnStageLog,
	Campaign,
	AutomationConfig,
	APISetting,
)
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import csv
import io
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.conf import settings
from django.utils.text import slugify
from datetime import datetime
from django.utils import timezone
from datetime import timedelta

INDIA_STATE_CODES = {
    'andhra pradesh': 'IN-AP',
    'arunachal pradesh': 'IN-AR',
    'assam': 'IN-AS',
    'bihar': 'IN-BR',
    'chhattisgarh': 'IN-CT',
    'goa': 'IN-GA',
    'gujarat': 'IN-GJ',
    'haryana': 'IN-HR',
    'himachal pradesh': 'IN-HP',
    'jharkhand': 'IN-JH',
    'karnataka': 'IN-KA',
    'kerala': 'IN-KL',
    'madhya pradesh': 'IN-MP',
    'maharashtra': 'IN-MH',
    'manipur': 'IN-MN',
    'meghalaya': 'IN-ML',
    'mizoram': 'IN-MZ',
    'nagaland': 'IN-NL',
    'odisha': 'IN-OR',
    'punjab': 'IN-PB',
    'rajasthan': 'IN-RJ',
    'sikkim': 'IN-SK',
    'tamil nadu': 'IN-TN',
    'telangana': 'IN-TG',
    'tripura': 'IN-TR',
    'uttar pradesh': 'IN-UP',
    'uttarakhand': 'IN-UT',
    'west bengal': 'IN-WB',
    'delhi': 'IN-DL',
    'jammu and kashmir': 'IN-JK',
    'ladakh': 'IN-LA',
    'andaman and nicobar islands': 'IN-AN',
    'chandigarh': 'IN-CH',
    'dadra and nagar haveli and daman and diu': 'IN-DH',
    'lakshadweep': 'IN-LD',
    'puducherry': 'IN-PY',
}

@staff_member_required
def search_api(request):
    """Global search API for admin dashboard"""
    query = request.GET.get('q', '').strip()
    
    if not query:
        return JsonResponse({'results': []})
    
    results = []
    
    # Search orders by ID
    if query.isdigit():
        orders = Order.objects.filter(id=query)[:5]
        for order in orders:
            results.append({
                'type': 'order',
                'id': order.id,
                'title': f'Order #{order.id}',
                'subtitle': f'{order.user.email} - ${order.total}',
                'url': f'/admin-dashboard/#orders'
            })
    
    # Search orders by customer email
    orders = Order.objects.filter(
        Q(user__email__icontains=query) | 
        Q(user__first_name__icontains=query) |
        Q(user__last_name__icontains=query)
    )[:5]
    
    for order in orders:
        results.append({
            'type': 'order',
            'id': order.id,
            'title': f'Order #{order.id}',
            'subtitle': f'{order.user.email} - ${order.total}',
            'url': f'/admin-dashboard/#orders'
        })
    
    # Search products
    products = Product.objects.filter(
        Q(name__icontains=query) |
        Q(description__icontains=query)
    )[:5]
    
    for product in products:
        results.append({
            'type': 'product',
            'id': product.id,
            'title': product.name,
            'subtitle': f'{product.category.name} - ${product.price}',
            'url': f'/admin-dashboard/#products'
        })
    
    # Search customers
    customers = User.objects.filter(
        Q(email__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query),
        is_staff=False
    )[:5]
    
    for customer in customers:
        results.append({
            'type': 'customer',
            'id': customer.id,
            'title': f'{customer.first_name} {customer.last_name}',
            'subtitle': customer.email,
            'url': f'/admin-dashboard/#customers'
        })
    
    return JsonResponse({'results': results[:10]})

@staff_member_required
def export_orders(request):
    """Export orders to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="orders_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Order ID', 'Customer', 'Email', 'Phone', 'Address', 'Total', 'Status', 'Date'])
    
    orders = Order.objects.select_related('user').all()
    for order in orders:
        writer.writerow([
            order.id,
            f'{order.user.first_name} {order.user.last_name}',
            order.user.email,
            order.mobile_number or '-',
            order.shipping_address or '-',
            order.total,
            order.get_status_display(),
            order.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    return response

@staff_member_required
def export_products(request):
    """Export products to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="products_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Product ID', 'Name', 'Category', 'Price', 'Stock', 'Description'])
    
    products = Product.objects.select_related('category').all()
    for product in products:
        writer.writerow([
            product.id,
            product.name,
            product.category.name,
            product.price,
            product.stock,
            product.description[:100] + '...' if len(product.description) > 100 else product.description
        ])
    
    return response

@staff_member_required
def export_customers(request):
    """Export customers to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="customers_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Customer ID', 'Name', 'Email', 'Phone', 'Join Date', 'Total Orders', 'Lifetime Value'])
    
    from django.db.models import Count, Sum
    customers = User.objects.filter(is_staff=False).annotate(
        order_count=Count('order'),
        lifetime_value=Sum('order__total')
    )
    
    for customer in customers:
        phone = getattr(customer, 'userprofile', None)
        phone_number = phone.phone if phone else '-'
        
        writer.writerow([
            customer.id,
            f'{customer.first_name} {customer.last_name}',
            customer.email,
            phone_number,
            customer.date_joined.strftime('%Y-%m-%d'),
            customer.order_count or 0,
            customer.lifetime_value or 0
        ])
    
    return response

@staff_member_required
def add_product(request):
    """Add new product"""
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            description = request.POST.get('description', '')
            price = request.POST.get('price')
            cost_price = request.POST.get('cost_price', '0')
            category_id = request.POST.get('category')
            stock = request.POST.get('stock')
            low_stock_threshold = request.POST.get('low_stock_threshold', '5')
            image = request.FILES.get('image')
            
            if not all([name, price, category_id, stock]):
                return JsonResponse({'success': False, 'error': 'Missing required fields'})
            
            mrp = request.POST.get('mrp', '0')
            rating = request.POST.get('rating', '0')
            rating_count = request.POST.get('rating_count', '0')

            category = Category.objects.get(id=category_id, is_active=True)

            product = Product.objects.create(
                name=name,
                description=description,
                price=float(price),
                mrp=float(mrp or 0),
                cost_price=float(cost_price or 0),
                rating=float(rating or 0),
                rating_count=int(rating_count or 0),
                category=category,
                stock=int(stock),
                low_stock_threshold=int(low_stock_threshold or 5),
                is_active=request.POST.get('is_active', '1') in ['1', 'true', 'on', 'yes'],
                image=image
            )
            for extra in request.FILES.getlist('additional_images'):
                ProductImage.objects.create(product=product, image=extra)
            video_file = request.FILES.get('video')
            if video_file:
                ProductVideo.objects.create(product=product, video=video_file)
            
            return JsonResponse({'success': True, 'message': 'Product created successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@staff_member_required
def customer_detail_api(request, customer_id):
    """Get detailed customer information"""
    try:
        customer = get_object_or_404(User, id=customer_id)
        
        # Get customer orders
        orders = Order.objects.filter(user=customer).order_by('-created_at')
        
        # Calculate statistics
        total_orders = orders.count()
        lifetime_value = orders.aggregate(total=Sum('total'))['total'] or 0
        last_order = orders.first()
        
        # Get recent orders (last 5)
        recent_orders = orders[:5]
        
        # Get customer name
        customer_name = f"{customer.first_name} {customer.last_name}".strip()
        if not customer_name:
            customer_name = customer.username
            
        # Get phone number
        phone = None
        try:
            if hasattr(customer, 'userprofile') and customer.userprofile.phone:
                phone = customer.userprofile.phone
        except:
            pass
        
        customer_data = {
            'id': customer.id,
            'name': customer_name,
            'email': customer.email,
            'phone': phone,
            'join_date': customer.date_joined.strftime('%B %d, %Y'),
            'is_active': customer.is_active,
            'total_orders': total_orders,
            'lifetime_value': float(lifetime_value),
            'last_order_date': last_order.created_at.strftime('%B %d, %Y') if last_order else None,
            'recent_orders': [
                {
                    'id': order.id,
                    'total': float(order.total),
                    'status': order.status,
                    'date': order.created_at.strftime('%b %d, %Y')
                }
                for order in recent_orders
            ]
        }
        
        return JsonResponse({'success': True, 'customer': customer_data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@staff_member_required
def edit_product_api(request, product_id):
    """Edit product API"""
    if request.method == 'POST':
        try:
            product = get_object_or_404(Product, id=product_id)
            
            name = request.POST.get('name')
            description = request.POST.get('description')
            price = request.POST.get('price')
            category_id = request.POST.get('category')
            stock = request.POST.get('stock')
            cost_price = request.POST.get('cost_price')
            low_stock_threshold = request.POST.get('low_stock_threshold')
            mrp = request.POST.get('mrp')
            rating = request.POST.get('rating')
            rating_count = request.POST.get('rating_count')

            if not all([name, description, price, category_id, stock]):
                return JsonResponse({'success': False, 'error': 'All fields are required'})

            category = get_object_or_404(Category, id=category_id)

            # Update product fields
            product.name = name
            product.description = description
            product.price = float(price)
            product.category = category
            product.stock = int(stock)
            if cost_price is not None and cost_price != '':
                product.cost_price = float(cost_price)
            if low_stock_threshold is not None and low_stock_threshold != '':
                product.low_stock_threshold = int(low_stock_threshold)
            if mrp is not None and mrp != '':
                product.mrp = float(mrp)
            if rating is not None and rating != '':
                product.rating = float(rating)
            if rating_count is not None and rating_count != '':
                product.rating_count = int(rating_count)
            if request.POST.get('is_active') is not None:
                product.is_active = request.POST.get('is_active') in ['1', 'true', 'on', 'yes']
            
            if 'image' in request.FILES:
                product.image = request.FILES['image']

            product.save()

            for extra in request.FILES.getlist('additional_images'):
                ProductImage.objects.create(product=product, image=extra)

            delete_img_ids = request.POST.getlist('delete_image_ids')
            if delete_img_ids:
                ProductImage.objects.filter(product=product, id__in=delete_img_ids).delete()

            video_file = request.FILES.get('video')
            if video_file:
                product.videos.all().delete()
                ProductVideo.objects.create(product=product, video=video_file)

            return JsonResponse({'success': True, 'message': 'Product updated successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@staff_member_required
@require_http_methods(["POST"])
def toggle_product_active_api(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.is_active = not product.is_active
    product.save(update_fields=["is_active"])
    return JsonResponse({"success": True, "is_active": product.is_active})


@staff_member_required
def delete_product_api(request, product_id):
    """Delete product API"""
    if request.method == 'POST':
        try:
            product = get_object_or_404(Product, id=product_id)
            product_name = product.name
            product.delete()
            
            return JsonResponse({'success': True, 'message': f'Product "{product_name}" deleted successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@staff_member_required
def get_product_api(request, product_id):
    """Get product details for editing"""
    try:
        product = get_object_or_404(Product, id=product_id)
        
        product_data = {
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'price': float(product.price),
            'mrp': float(product.mrp),
            'sku': product.sku or '',
            'discount_percent': product.discount_percent,
            'rating': float(product.rating),
            'rating_count': product.rating_count,
            'category_id': product.category.id,
            'category_name': product.category.name,
            'stock': product.stock,
            'cost_price': float(product.cost_price),
            'low_stock_threshold': product.low_stock_threshold,
            'is_active': product.is_active,
            'image_url': product.image.url if product.image else None,
            'additional_images': [
                {'id': img.id, 'url': img.image.url}
                for img in product.additional_images.all()
            ],
            'videos': [
                {'id': v.id, 'url': v.video.url}
                for v in product.videos.all()
            ],
        }

        return JsonResponse({'success': True, 'product': product_data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@staff_member_required
def filter_orders(request):
    """Filter orders by status, date, etc."""
    status = request.GET.get('status')
    search = request.GET.get('search', '')
    
    orders = Order.objects.select_related('user').all()
    
    if status and status != 'all':
        orders = orders.filter(status=status)
    
    if search:
        orders = orders.filter(
            Q(id__icontains=search) |
            Q(user__email__icontains=search) |
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(mobile_number__icontains=search)
        )
    
    orders_data = []
    for order in orders.order_by('-created_at')[:50]:  # Limit to 50 results
        orders_data.append({
            'id': order.id,
            'customer': order.user.email,
            'phone': order.mobile_number or '-',
            'address': order.shipping_address or '-',
            'total': str(order.total),
            'status': order.status,
            'status_display': order.get_status_display(),
            'date': order.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return JsonResponse({'orders': orders_data})

@staff_member_required
def get_notifications(request):
    """Get notifications for admin dashboard"""
    notifications = Notification.objects.all()[:20]  # Last 20 notifications
    unread_count = Notification.objects.filter(is_read=False).count()
    
    notification_data = []
    for notif in notifications:
        # Determine icon and color based on type
        icon_map = {
            'order_placed': 'fa-shopping-cart',
            'order_cancelled': 'fa-times-circle', 
            'low_stock': 'fa-exclamation-triangle',
            'new_customer': 'fa-user-plus'
        }
        
        color_map = {
            'order_placed': '#10b981',
            'order_cancelled': '#ef4444',
            'low_stock': '#f59e0b', 
            'new_customer': '#2563eb'
        }
        
        notification_data.append({
            'id': notif.id,
            'title': notif.title,
            'message': notif.message,
            'time': notif.created_at.strftime('%M minutes ago') if notif.created_at > timezone.now() - timedelta(hours=1) else notif.created_at.strftime('%b %d, %H:%M'),
            'read': notif.is_read,
            'icon': icon_map.get(notif.notification_type, 'fa-bell'),
            'color': color_map.get(notif.notification_type, '#64748b')
        })
    
    return JsonResponse({
        'notifications': notification_data,
        'count': unread_count
    })

@staff_member_required
def mark_notification_read(request, notification_id):
    """Mark notification as read"""
    if request.method == 'POST':
        try:
            notification = Notification.objects.get(id=notification_id)
            notification.is_read = True
            notification.save()
            return JsonResponse({'success': True})
        except Notification.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Notification not found'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@staff_member_required
def mark_all_notifications_read(request):
    """Mark all notifications as read"""
    if request.method == 'POST':
        Notification.objects.filter(is_read=False).update(is_read=True)
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@staff_member_required
@require_http_methods(["GET", "POST"])
def categories_api(request):
    if request.method == "GET":
        categories = Category.objects.all().order_by("name")
        return JsonResponse(
            {
                "success": True,
                "categories": [
                    {
                        "id": c.id,
                        "name": c.name,
                        "is_active": c.is_active,
                        "product_count": c.products.count(),
                    }
                    for c in categories
                ],
            }
        )

    name = (request.POST.get("name") or "").strip()
    if not name:
        return JsonResponse({"success": False, "error": "Category name is required"})

    category, created = Category.objects.get_or_create(name=name)
    if not category.is_active:
        category.is_active = True
        category.save(update_fields=["is_active"])
    return JsonResponse(
        {
            "success": True,
            "created": created,
            "category": {"id": category.id, "name": category.name, "is_active": category.is_active},
        }
    )


@staff_member_required
@require_http_methods(["POST"])
def delete_category_api(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    category.is_active = False
    category.save(update_fields=["is_active"])
    return JsonResponse({"success": True})


@staff_member_required
@require_http_methods(["POST"])
def categories_update_api(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    try:
        body = json.loads(request.body)
    except Exception:
        body = {}
    new_name = (body.get("name") or request.POST.get("name") or "").strip()
    if new_name and new_name != category.name:
        if Category.objects.filter(name=new_name).exclude(id=category_id).exists():
            return JsonResponse({"success": False, "error": "Category name already exists"})
        category.name = new_name
    if "is_active" in body:
        category.is_active = bool(body["is_active"])
    category.save()
    return JsonResponse({"success": True, "category": {"id": category.id, "name": category.name, "is_active": category.is_active}})


@staff_member_required
@require_http_methods(["POST"])
def categories_toggle_api(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    category.is_active = not category.is_active
    category.save(update_fields=["is_active"])
    return JsonResponse({"success": True, "is_active": category.is_active})


@staff_member_required
@require_http_methods(["GET"])
def categories_products_api(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(category=category).order_by("name")
    result = []
    for p in products:
        image_url = None
        if p.image:
            try:
                image_url = p.image.url
            except Exception:
                pass
        result.append({
            "id": p.id,
            "name": p.name,
            "price": float(p.price),
            "cost_price": float(p.cost_price),
            "stock": p.stock,
            "is_active": p.is_active,
            "image_url": image_url,
        })
    return JsonResponse({
        "success": True,
        "category": {"id": category.id, "name": category.name},
        "products": result,
    })


@staff_member_required
@require_http_methods(["GET"])
def product_status_trend_api(request):
    from datetime import date
    today = date.today()
    labels = []
    active_counts = []
    disabled_counts = []
    out_of_stock_counts = []
    for i in range(5, -1, -1):
        # Get the start of each of the last 6 months
        if today.month - i <= 0:
            month = today.month - i + 12
            year = today.year - 1
        else:
            month = today.month - i
            year = today.year
        month_label = date(year, month, 1).strftime("%b")
        # Count products created on or before end of that month
        import calendar
        last_day = calendar.monthrange(year, month)[1]
        end_of_month = date(year, month, last_day)
        base_qs = Product.objects.filter(created_at__date__lte=end_of_month)
        labels.append(month_label)
        active_counts.append(base_qs.filter(is_active=True).count())
        disabled_counts.append(base_qs.filter(is_active=False).count())
        out_of_stock_counts.append(base_qs.filter(stock=0).count())

    return JsonResponse({
        "success": True,
        "labels": labels,
        "active": active_counts,
        "disabled": disabled_counts,
        "out_of_stock": out_of_stock_counts,
    })


@staff_member_required
@require_http_methods(["GET"])
def top_categories_revenue_api(request):
    from datetime import date, timedelta
    end_date = date.today()
    start_date = end_date - timedelta(days=365)
    revenue_by_cat = (
        OrderItem.objects.filter(
            order__status="delivered",
            order__created_at__date__gte=start_date,
        )
        .values("product__category__name")
        .annotate(total_revenue=Sum(F("price") * F("quantity")))
        .order_by("-total_revenue")[:10]
    )
    data = [
        {
            "category": item["product__category__name"] or "Uncategorized",
            "revenue": float(item["total_revenue"] or 0),
        }
        for item in revenue_by_cat
    ]
    return JsonResponse({"success": True, "data": data})


@staff_member_required
@require_http_methods(["GET", "POST"])
def reels_api(request):
    if request.method == "GET":
        reels = InstagramReel.objects.all()
        return JsonResponse(
            {
                "success": True,
                "reels": [
                    {
                        "id": r.id,
                        "title": r.title,
                        "is_active": r.is_active,
                        "sort_order": r.sort_order,
                        "video": r.get_video_source(),
                        "thumbnail": r.thumbnail.url if r.thumbnail else None,
                    }
                    for r in reels
                ],
            }
        )

    title = (request.POST.get("title") or "").strip()
    video_url = (request.POST.get("video_url") or "").strip()
    sort_order = int(request.POST.get("sort_order") or 0)
    is_active = request.POST.get("is_active") in ["1", "true", "on", "yes"]
    video = request.FILES.get("video")
    thumbnail = request.FILES.get("thumbnail")

    if not (video or video_url):
        return JsonResponse({"success": False, "error": "Video or Video URL is required"})

    reel = InstagramReel.objects.create(
        title=title,
        video=video,
        video_url=video_url,
        thumbnail=thumbnail,
        sort_order=sort_order,
        is_active=is_active,
    )
    return JsonResponse({"success": True, "id": reel.id})


@staff_member_required
@require_http_methods(["POST"])
def toggle_reel_api(request, reel_id):
    reel = get_object_or_404(InstagramReel, id=reel_id)
    reel.is_active = not reel.is_active
    reel.save(update_fields=["is_active"])
    return JsonResponse({"success": True, "is_active": reel.is_active})


@staff_member_required
@require_http_methods(["POST"])
def delete_reel_api(request, reel_id):
    reel = get_object_or_404(InstagramReel, id=reel_id)
    reel.delete()
    return JsonResponse({"success": True})


@staff_member_required
@require_http_methods(["GET", "POST"])
def trust_badges_api(request):
    if request.method == "GET":
        badges = TrustBadge.objects.all()
        return JsonResponse(
            {
                "success": True,
                "badges": [
                    {
                        "id": b.id,
                        "title": b.title,
                        "subtitle": b.subtitle,
                        "is_active": b.is_active,
                        "sort_order": b.sort_order,
                        "icon_image": b.icon_image.url if b.icon_image else None,
                    }
                    for b in badges
                ],
            }
        )

    title = (request.POST.get("title") or "").strip()
    subtitle = (request.POST.get("subtitle") or "").strip()
    sort_order = int(request.POST.get("sort_order") or 0)
    is_active = request.POST.get("is_active") in ["1", "true", "on", "yes"]
    icon_image = request.FILES.get("icon_image")

    if not title:
        return JsonResponse({"success": False, "error": "Title is required"})

    badge = TrustBadge.objects.create(
        title=title,
        subtitle=subtitle,
        sort_order=sort_order,
        is_active=is_active,
        icon_image=icon_image,
    )
    return JsonResponse({"success": True, "id": badge.id})


@staff_member_required
@require_http_methods(["POST"])
def delete_trust_badge_api(request, badge_id):
    badge = get_object_or_404(TrustBadge, id=badge_id)
    badge.delete()
    return JsonResponse({"success": True})


@staff_member_required
@require_http_methods(["GET", "POST"])
def marketing_spend_api(request):
    if request.method == "GET":
        spends = MarketingSpend.objects.all()[:200]
        return JsonResponse(
            {
                "success": True,
                "spends": [
                    {
                        "id": s.id,
                        "source": s.source,
                        "source_label": s.get_source_display(),
                        "campaign": s.campaign,
                        "amount": float(s.amount),
                        "spend_date": s.spend_date.isoformat(),
                        "notes": s.notes,
                    }
                    for s in spends
                ],
            }
        )

    try:
        amount = float(request.POST.get("amount") or 0)
    except ValueError:
        amount = 0
    spend_date = request.POST.get("spend_date")
    source = request.POST.get("source") or "meta"
    campaign = (request.POST.get("campaign") or "").strip()
    notes = (request.POST.get("notes") or "").strip()

    if amount <= 0 or not spend_date:
        return JsonResponse({"success": False, "error": "Amount and date are required"})

    spend = MarketingSpend.objects.create(
        source=source,
        campaign=campaign,
        amount=amount,
        spend_date=spend_date,
        notes=notes,
    )
    return JsonResponse({"success": True, "id": spend.id})


@staff_member_required
@require_http_methods(["GET", "POST"])
def expense_ledger_api(request):
    if request.method == "GET":
        entries = ExpenseEntry.objects.all()[:200]
        return JsonResponse(
            {
                "success": True,
                "entries": [
                    {
                        "id": e.id,
                        "category": e.category,
                        "category_label": e.get_category_display(),
                        "title": e.title,
                        "amount": float(e.amount),
                        "expense_date": e.expense_date.isoformat(),
                        "notes": e.notes,
                    }
                    for e in entries
                ],
            }
        )

    try:
        amount = float(request.POST.get("amount") or 0)
    except ValueError:
        amount = 0
    expense_date = request.POST.get("expense_date")
    category = request.POST.get("category") or "other"
    title = (request.POST.get("title") or "").strip()
    notes = (request.POST.get("notes") or "").strip()

    if amount <= 0 or not expense_date or not title:
        return JsonResponse({"success": False, "error": "Title, amount and date are required"})

    entry = ExpenseEntry.objects.create(
        category=category,
        title=title,
        amount=amount,
        expense_date=expense_date,
        notes=notes,
    )
    return JsonResponse({"success": True, "id": entry.id})


@staff_member_required
@require_http_methods(["GET"])
def profit_loss_api(request):
    """
    Month-wise P&L for admin graphs.
    Query params:
      - month=YYYY-MM (optional)
    """
    month = (request.GET.get("month") or "").strip()
    if month:
        start = datetime.strptime(month + "-01", "%Y-%m-%d").date()
        # next month
        if start.month == 12:
            end = start.replace(year=start.year + 1, month=1, day=1)
        else:
            end = start.replace(month=start.month + 1, day=1)
    else:
        today = timezone.localdate()
        start = today.replace(day=1)
        if start.month == 12:
            end = start.replace(year=start.year + 1, month=1, day=1)
        else:
            end = start.replace(month=start.month + 1, day=1)

    revenue = (
        Order.objects.filter(status="delivered", created_at__date__gte=start, created_at__date__lt=end)
        .aggregate(total=Sum("total"))
        .get("total")
        or 0
    )
    marketing = (
        MarketingSpend.objects.filter(spend_date__gte=start, spend_date__lt=end)
        .aggregate(total=Sum("amount"))
        .get("total")
        or 0
    )
    expenses = (
        ExpenseEntry.objects.filter(expense_date__gte=start, expense_date__lt=end)
        .aggregate(total=Sum("amount"))
        .get("total")
        or 0
    )
    cogs_expr = ExpressionWrapper(
        F("quantity") * F("product__cost_price"),
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )
    cogs = (
        OrderItem.objects.filter(
            order__status="delivered",
            order__created_at__date__gte=start,
            order__created_at__date__lt=end,
        )
        .aggregate(total=Sum(cogs_expr))
        .get("total")
        or 0
    )
    gross = revenue - cogs
    net = revenue - (cogs + marketing + expenses)

    return JsonResponse(
        {
            "success": True,
            "range": {"start": start.isoformat(), "end": end.isoformat()},
            "revenue": float(revenue),
            "cogs": float(cogs),
            "gross_profit": float(gross),
            "marketing": float(marketing),
            "expenses": float(expenses),
            "net_profit": float(net),
        }
    )


@staff_member_required
@require_http_methods(["GET", "POST"])
def reviews_admin_api(request):
    if request.method == "GET":
        status = (request.GET.get("status") or "pending").strip()
        qs = ProductReview.objects.select_related("product", "user")
        if status == "pending":
            qs = qs.filter(is_approved=False)
        elif status == "approved":
            qs = qs.filter(is_approved=True)

        reviews = qs.order_by("-created_at")[:200]
        return JsonResponse(
            {
                "success": True,
                "reviews": [
                    {
                        "id": r.id,
                        "product": r.product.name,
                        "user": r.user.username,
                        "rating": r.rating,
                        "reviewer_name": r.reviewer_name,
                        "reviewer_image": r.reviewer_image.url if r.reviewer_image else "",
                        "title": r.title,
                        "body": r.body,
                        "is_approved": r.is_approved,
                        "is_visible": r.is_visible,
                        "created_at": r.created_at.strftime("%Y-%m-%d %H:%M"),
                    }
                    for r in reviews
                ],
            }
        )

    action = request.POST.get("action")
    if action == "create":
        product_id = request.POST.get("product_id")
        rating = int(request.POST.get("rating") or 5)
        title = (request.POST.get("title") or "").strip()
        body = (request.POST.get("body") or "").strip()
        is_approved = str(request.POST.get("is_approved") or "1").lower() in ["1", "true", "yes", "on"]
        is_visible = str(request.POST.get("is_visible") or "1").lower() in ["1", "true", "yes", "on"]
        reviewer_name = (request.POST.get("reviewer_name") or "").strip()
        if not product_id or not body:
            return JsonResponse({"success": False, "error": "Product and review text are required"})
        review = ProductReview.objects.create(
            product_id=product_id,
            user=request.user,
            rating=max(1, min(5, rating)),
            title=title,
            body=body,
            reviewer_name=reviewer_name,
            is_approved=is_approved,
            is_visible=is_visible,
        )
        if request.FILES.get("reviewer_image"):
            review.reviewer_image = request.FILES["reviewer_image"]
            review.save(update_fields=["reviewer_image"])
        return JsonResponse({"success": True, "id": review.id})
    if action == "edit":
        review_id = request.POST.get("review_id")
        review = get_object_or_404(ProductReview, id=review_id)
        review.rating = max(1, min(5, int(request.POST.get("rating") or review.rating)))
        review.title = (request.POST.get("title") or "").strip()
        review.body = (request.POST.get("body") or "").strip()
        review.reviewer_name = (request.POST.get("reviewer_name") or "").strip()
        review.is_approved = str(request.POST.get("is_approved") or "0").lower() in ["1", "true", "yes", "on"]
        review.is_visible = str(request.POST.get("is_visible") or "0").lower() in ["1", "true", "yes", "on"]
        if request.FILES.get("reviewer_image"):
            review.reviewer_image = request.FILES["reviewer_image"]
        review.save()
        return JsonResponse({"success": True})

    review_id = request.POST.get("review_id")
    review = get_object_or_404(ProductReview, id=review_id)
    if action == "approve":
        review.is_approved = True
        review.save(update_fields=["is_approved"])
    elif action == "toggle_visibility":
        value = str(request.POST.get("value") or "").strip()
        if value in ["0", "1"]:
            review.is_approved = value == "1"
        else:
            review.is_approved = not review.is_approved
        review.save(update_fields=["is_approved"])
    elif action == "toggle_active":
        value = str(request.POST.get("value") or "").strip()
        if value in ["0", "1"]:
            review.is_visible = value == "1"
        else:
            review.is_visible = not review.is_visible
        review.save(update_fields=["is_visible"])
    elif action == "reject":
        review.delete()
        return JsonResponse({"success": True, "deleted": True})
    else:
        return JsonResponse({"success": False, "error": "Invalid action"})

    return JsonResponse({"success": True, "is_approved": review.is_approved})


@staff_member_required
@require_http_methods(["GET", "POST"])
def announcements_api(request):
    if request.method == "GET":
        items = Announcement.objects.order_by("-created_at")[:200]
        return JsonResponse(
            {
                "success": True,
                "items": [
                    {
                        "id": a.id,
                        "title": a.title,
                        "message": a.message,
                        "is_active": a.is_active,
                        "created_at": a.created_at.strftime("%Y-%m-%d %H:%M"),
                    }
                    for a in items
                ],
            }
        )
    action = (request.POST.get("action") or "create").strip()
    if action == "create":
        message = (request.POST.get("message") or "").strip()
        if not message:
            return JsonResponse({"success": False, "error": "Message is required"})
        Announcement.objects.create(
            title=(request.POST.get("title") or "").strip(),
            message=message,
            is_active=str(request.POST.get("is_active") or "1").lower() in ["1", "true", "yes", "on"],
        )
        return JsonResponse({"success": True})
    if action == "edit":
        item = get_object_or_404(Announcement, id=request.POST.get("announcement_id"))
        message = (request.POST.get("message") or "").strip()
        if not message:
            return JsonResponse({"success": False, "error": "Message is required"})
        item.title = (request.POST.get("title") or "").strip()
        item.message = message
        item.is_active = str(request.POST.get("is_active") or "1").lower() in ["1", "true", "yes", "on"]
        item.save()
        return JsonResponse({"success": True})
    if action == "toggle":
        item = get_object_or_404(Announcement, id=request.POST.get("announcement_id"))
        item.is_active = not item.is_active
        item.save(update_fields=["is_active"])
        return JsonResponse({"success": True, "is_active": item.is_active})
    if action == "delete":
        item = get_object_or_404(Announcement, id=request.POST.get("announcement_id"))
        item.delete()
        return JsonResponse({"success": True})
    return JsonResponse({"success": False, "error": "Invalid action"})


@staff_member_required
@require_http_methods(["GET"])
def wishlist_analytics_api(request):
    days = int(request.GET.get("days") or 30)
    since = timezone.now() - timedelta(days=days)

    top = (
        WishlistItem.objects.filter(created_at__gte=since)
        .values("product__id", "product__name")
        .annotate(count=Count("id"))
        .order_by("-count")[:10]
    )

    daily = (
        WishlistItem.objects.filter(created_at__gte=since)
        .extra({"day": "date(created_at)"})
        .values("day")
        .annotate(count=Count("id"))
        .order_by("day")
    )

    return JsonResponse(
        {
            "success": True,
            "top": list(top),
            "daily": [{"day": str(d["day"]), "count": d["count"]} for d in daily],
        }
    )


@staff_member_required
@require_http_methods(["GET", "POST"])
def homepage_section_content_api(request):
    if request.method == "GET":
        items = HomepageSectionContent.objects.all()
        return JsonResponse(
            {
                "success": True,
                "items": [
                    {
                        "id": item.id,
                        "section_key": item.section_key,
                        "section_label": item.get_section_key_display(),
                        "title": item.title,
                        "subtitle": item.subtitle,
                        "button_text": item.button_text,
                        "button_url": item.button_url,
                        "secondary_button_text": item.secondary_button_text,
                        "secondary_button_url": item.secondary_button_url,
                        "background_image": item.background_image.url if item.background_image else None,
                        "background_video": item.background_video.url if item.background_video else None,
                        "is_active": item.is_active,
                    }
                    for item in items
                ],
            }
        )

    section_key = request.POST.get("section_key")
    if not section_key:
        return JsonResponse({"success": False, "error": "Section key is required"})

    item, _ = HomepageSectionContent.objects.get_or_create(section_key=section_key)
    item.title = request.POST.get("title", "")
    item.subtitle = request.POST.get("subtitle", "")
    item.button_text = request.POST.get("button_text", "")
    item.button_url = request.POST.get("button_url", "")
    item.secondary_button_text = request.POST.get("secondary_button_text", "")
    item.secondary_button_url = request.POST.get("secondary_button_url", "")
    item.is_active = request.POST.get("is_active") in ["1", "true", "on", "yes"]
    if request.FILES.get("background_image"):
        item.background_image = request.FILES["background_image"]
    if request.FILES.get("background_video"):
        item.background_video = request.FILES["background_video"]
    item.save()
    return JsonResponse({"success": True, "id": item.id})


@staff_member_required
@require_http_methods(["GET", "POST"])
def homepage_section_products_api(request):
    if request.method == "GET":
        items = HomepageSectionProduct.objects.select_related("product").all()
        return JsonResponse(
            {
                "success": True,
                "items": [
                    {
                        "id": item.id,
                        "section_type": item.section_type,
                        "section_label": item.get_section_type_display(),
                        "product_id": item.product_id,
                        "product_name": item.product.name,
                        "position": item.position,
                        "is_active": item.is_active,
                    }
                    for item in items
                ],
            }
        )

    try:
        position = int(request.POST.get("position") or 1)
    except ValueError:
        position = 1
    section_type = request.POST.get("section_type")
    product_id = request.POST.get("product_id")
    if not section_type or not product_id:
        return JsonResponse({"success": False, "error": "Section and product are required"})
    product = get_object_or_404(Product, id=product_id)
    item = HomepageSectionProduct.objects.create(
        section_type=section_type,
        product=product,
        position=position,
        is_active=True,
    )
    return JsonResponse({"success": True, "id": item.id})


@staff_member_required
@require_http_methods(["POST"])
def delete_homepage_section_product_api(request, item_id):
    item = get_object_or_404(HomepageSectionProduct, id=item_id)
    item.delete()
    return JsonResponse({"success": True})


@staff_member_required
@require_http_methods(["GET"])
def india_state_order_counts_api(request):
    counts = (
        Order.objects.exclude(shipping_state__isnull=True)
        .exclude(shipping_state__exact="")
        .values("shipping_state")
        .annotate(total=Count("id"))
        .order_by("-total")
    )
    items = []
    max_count = 0
    for entry in counts:
        state_name = (entry["shipping_state"] or "").strip()
        total = entry["total"]
        max_count = max(max_count, total)
        code = INDIA_STATE_CODES.get(state_name.lower())
        items.append(
            {
                "state": state_name,
                "code": code,
                "total": total,
            }
        )

    return JsonResponse(
        {
            "success": True,
            "max_count": max_count,
            "items": items,
        }
    )


@staff_member_required
@require_http_methods(["GET"])
def low_stock_products_api(request):
    products = Product.objects.filter(stock__lte=F("low_stock_threshold")).order_by("stock", "name")
    return JsonResponse(
        {
            "success": True,
            "items": [
                {
                    "id": p.id,
                    "name": p.name,
                    "stock": p.stock,
                    "threshold": p.low_stock_threshold,
                    "is_active": p.is_active,
                }
                for p in products
            ],
        }
    )


@staff_member_required
@require_http_methods(["GET", "POST"])
def product_images_api(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == "GET":
        images = product.additional_images.all()
        return JsonResponse(
            {
                "success": True,
                "items": [
                    {
                        "id": i.id,
                        "url": i.image.url,
                        "is_primary": i.is_primary,
                        "sort_order": i.sort_order,
                    }
                    for i in images if i.image
                ],
            }
        )

    files = request.FILES.getlist("images")
    if not files:
        return JsonResponse({"success": False, "error": "No images uploaded"})
    current_count = product.additional_images.count()
    for index, f in enumerate(files[:6]):
        ProductImage.objects.create(
            product=product,
            image=f,
            sort_order=current_count + index,
            is_primary=(current_count == 0 and index == 0),
        )
    return JsonResponse({"success": True})


@staff_member_required
@require_http_methods(["POST"])
def delete_product_image_api(request, image_id):
    image = get_object_or_404(ProductImage, id=image_id)
    image.delete()
    return JsonResponse({"success": True})


@staff_member_required
@require_http_methods(["POST"])
def set_primary_product_image_api(request, image_id):
    image = get_object_or_404(ProductImage, id=image_id)
    ProductImage.objects.filter(product=image.product).update(is_primary=False)
    image.is_primary = True
    image.save(update_fields=["is_primary"])
    return JsonResponse({"success": True})


@staff_member_required
@require_http_methods(["POST"])
def reorder_product_images_api(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    order = request.POST.get("order", "")
    image_ids = []
    for token in order.split(","):
        token = token.strip()
        if token.isdigit():
            image_ids.append(int(token))
    if not image_ids:
        return JsonResponse({"success": False, "error": "No order data provided"})
    images = {img.id: img for img in product.additional_images.all()}
    for idx, image_id in enumerate(image_ids):
        img = images.get(image_id)
        if img:
            img.sort_order = idx
            img.save(update_fields=["sort_order"])
    return JsonResponse({"success": True})


@staff_member_required
@require_http_methods(["GET", "POST"])
def product_variants_api(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == "GET":
        variants = product.variants.all()
        return JsonResponse(
            {
                "success": True,
                "items": [
                    {
                        "id": v.id,
                        "name": v.name,
                        "price_delta": float(v.price_delta),
                        "stock": v.stock,
                        "is_active": v.is_active,
                        "sort_order": v.sort_order,
                    }
                    for v in variants
                ],
            }
        )

    name = (request.POST.get("name") or "").strip()
    if not name:
        return JsonResponse({"success": False, "error": "Variant name required"})
    try:
        price_delta = float(request.POST.get("price_delta") or 0)
        stock = int(request.POST.get("stock") or 0)
        sort_order = int(request.POST.get("sort_order") or 0)
    except ValueError:
        return JsonResponse({"success": False, "error": "Invalid numeric value"})
    variant = ProductVariant.objects.create(
        product=product,
        name=name,
        price_delta=price_delta,
        stock=stock,
        sort_order=sort_order,
        is_active=request.POST.get("is_active") in ["1", "true", "on", "yes"],
    )
    return JsonResponse({"success": True, "id": variant.id})


@staff_member_required
@require_http_methods(["POST"])
def delete_variant_api(request, variant_id):
    variant = get_object_or_404(ProductVariant, id=variant_id)
    variant.delete()
    return JsonResponse({"success": True})


@staff_member_required
@require_http_methods(["POST"])
def toggle_homepage_section_product_api(request, item_id):
    item = get_object_or_404(HomepageSectionProduct, id=item_id)
    item.is_active = not item.is_active
    item.save(update_fields=["is_active"])
    return JsonResponse({"success": True, "is_active": item.is_active})


@staff_member_required
@require_http_methods(["POST"])
def update_homepage_section_product_api(request, item_id):
    item = get_object_or_404(HomepageSectionProduct, id=item_id)
    try:
        position = int(request.POST.get("position") or item.position)
    except ValueError:
        position = item.position
    item.position = max(1, position)
    item.section_type = request.POST.get("section_type") or item.section_type
    item.save(update_fields=["position", "section_type"])
    return JsonResponse({"success": True})


@staff_member_required
@require_http_methods(["GET"])
def order_lifecycle_logs_api(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    logs = order.lifecycle_logs.select_related("created_by").all()
    return JsonResponse(
        {
            "success": True,
            "order_status": order.status,
            "assigned_to": order.assigned_to_id,
            "logs": [
                {
                    "id": log.id,
                    "event_type": log.event_type,
                    "previous_status": log.previous_status,
                    "new_status": log.new_status,
                    "note": log.note,
                    "created_by": log.created_by.username if log.created_by else "System",
                    "created_at": log.created_at.strftime("%Y-%m-%d %H:%M"),
                }
                for log in logs
            ],
            "staff": [
                {"id": u.id, "name": u.get_full_name() or u.username}
                for u in User.objects.filter(is_staff=True).order_by("username")
            ],
        }
    )


@staff_member_required
@require_http_methods(["POST"])
def order_lifecycle_update_api(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    action = request.POST.get("action")
    if action == "assign":
        assignee_id = request.POST.get("assignee_id")
        assignee = User.objects.filter(id=assignee_id, is_staff=True).first() if assignee_id else None
        order.assigned_to = assignee
        order.save(update_fields=["assigned_to"])
        OrderLifecycleLog.objects.create(
            order=order,
            event_type="assignment",
            note=f"Assigned to {(assignee.get_full_name() or assignee.username) if assignee else 'Unassigned'}",
            created_by=request.user,
        )
        return JsonResponse({"success": True})

    if action == "status":
        new_status = request.POST.get("status")
        valid = [s[0] for s in Order.STATUS_CHOICES]
        if new_status not in valid:
            return JsonResponse({"success": False, "error": "Invalid status"})
        prev = order.status
        order.status = new_status
        update_fields = ["status", "updated_at"]
        # Auto-stamp the corresponding timestamp the first time each status is set
        ts_map = {
            "packed": "packed_at",
            "shipped": "shipped_at",
            "out_for_delivery": "out_for_delivery_at",
            "delivered": "delivered_at",
        }
        if new_status in ts_map:
            field = ts_map[new_status]
            if not getattr(order, field):
                setattr(order, field, timezone.now())
                update_fields.append(field)
        order.save(update_fields=update_fields)
        OrderLifecycleLog.objects.create(
            order=order,
            event_type="status_change",
            previous_status=prev,
            new_status=new_status,
            note=f"Status changed from {prev} to {new_status}",
            created_by=request.user,
        )
        return JsonResponse({"success": True})

    if action == "note":
        note = (request.POST.get("note") or "").strip()
        if not note:
            return JsonResponse({"success": False, "error": "Note is required"})
        OrderLifecycleLog.objects.create(
            order=order,
            event_type="internal_note",
            note=note,
            created_by=request.user,
        )
        return JsonResponse({"success": True})

    return JsonResponse({"success": False, "error": "Invalid action"})


@staff_member_required
@require_http_methods(["GET"])
def purchase_analytics_api(request):
    days = int(request.GET.get("days") or 30)
    since = timezone.now() - timedelta(days=days)
    daily = (
        Order.objects.filter(status="delivered", created_at__gte=since)
        .extra({"day": "date(created_at)"})
        .values("day")
        .annotate(count=Count("id"))
        .order_by("day")
    )
    return JsonResponse(
        {
            "success": True,
            "daily": [{"day": str(d["day"]), "count": d["count"]} for d in daily],
        }
    )


@staff_member_required
@require_http_methods(["GET"])
def dashboard_graphs_api(request):
    start = request.GET.get("start")
    end = request.GET.get("end")
    period = (request.GET.get("period") or "monthly").lower()
    order_qs = Order.objects.filter(status="delivered")
    wishlist_qs = WishlistItem.objects.all()
    if start:
        order_qs = order_qs.filter(created_at__date__gte=start)
        wishlist_qs = wishlist_qs.filter(created_at__date__gte=start)
    if end:
        order_qs = order_qs.filter(created_at__date__lte=end)
        wishlist_qs = wishlist_qs.filter(created_at__date__lte=end)

    if period in ["yearly", "monthly"]:
        sales_grouped = (
            order_qs.annotate(day=TruncMonth("created_at"))
            .values("day")
            .annotate(total_sales=Sum("total"))
            .order_by("day")
        )
        sales = [
            {"day": d["day"].strftime("%Y-%m"), "value": float(d["total_sales"] or 0)}
            for d in sales_grouped
            if d["day"]
        ][-12:]
    else:
        sales_grouped = (
            order_qs.annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(total_sales=Sum("total"))
            .order_by("day")
        )
        limit = 7 if period == "daily" else 8
        sales = [
            {"day": d["day"].strftime("%Y-%m-%d"), "value": float(d["total_sales"] or 0)}
            for d in sales_grouped
            if d["day"]
        ][-limit:]

    wishlist_counts = wishlist_qs.values("user_id").annotate(wishlist_count=Count("id"))
    order_counts = (
        order_qs
        .values("user_id")
        .annotate(order_count=Count("id"))
    )
    user_map = {}
    for w in wishlist_counts:
        user_map[w["user_id"]] = {"wishlist": w["wishlist_count"], "orders": 0}
    for o in order_counts:
        row = user_map.setdefault(o["user_id"], {"wishlist": 0, "orders": 0})
        row["orders"] = o["order_count"]
    users = User.objects.filter(id__in=list(user_map.keys())).only("id", "username", "first_name", "last_name")
    name_map = {u.id: (u.get_full_name().strip() or u.username) for u in users}
    wishlist_vs_orders = sorted(
        [
            {
                "user": name_map.get(uid, f"User {uid}"),
                "wishlist": vals["wishlist"],
                "orders": vals["orders"],
                "activity": vals["wishlist"] + vals["orders"],
            }
            for uid, vals in user_map.items()
        ],
        key=lambda x: x["activity"],
        reverse=True,
    )[:10]
    for row in wishlist_vs_orders:
        row.pop("activity", None)

    return JsonResponse(
        {
            "success": True,
            "sales": sales,
            "wishlist_vs_orders": wishlist_vs_orders,
        }
    )


@staff_member_required
@require_http_methods(["GET"])
def dashboard_kpis_api(request):
    period = (request.GET.get("period") or "monthly").lower()
    now = timezone.now()
    period_days = {
        "daily": 1,
        "weekly": 7,
        "monthly": 30,
        "yearly": 365,
    }
    days = period_days.get(period, 30)
    start = now - timedelta(days=days)
    previous_start = start - timedelta(days=days)

    delivered_now = Order.objects.filter(status="delivered", created_at__gte=start)
    delivered_prev = Order.objects.filter(
        status="delivered", created_at__gte=previous_start, created_at__lt=start
    )
    orders_now = Order.objects.filter(created_at__gte=start)
    orders_prev = Order.objects.filter(created_at__gte=previous_start, created_at__lt=start)

    earnings_now = float(delivered_now.aggregate(total=Sum("total"))["total"] or 0)
    earnings_prev = float(delivered_prev.aggregate(total=Sum("total"))["total"] or 0)
    total_orders_now = orders_now.count()
    total_orders_prev = orders_prev.count()
    customers_now = orders_now.values("user_id").distinct().count()
    customers_prev = orders_prev.values("user_id").distinct().count()

    delivered_items_now = OrderItem.objects.filter(order__in=delivered_now).annotate(
        line_cost=ExpressionWrapper(F("quantity") * F("product__cost_price"), output_field=DecimalField(max_digits=12, decimal_places=2))
    )
    delivered_items_prev = OrderItem.objects.filter(order__in=delivered_prev).annotate(
        line_cost=ExpressionWrapper(F("quantity") * F("product__cost_price"), output_field=DecimalField(max_digits=12, decimal_places=2))
    )
    cost_now = float(delivered_items_now.aggregate(total=Sum("line_cost"))["total"] or 0)
    cost_prev = float(delivered_items_prev.aggregate(total=Sum("line_cost"))["total"] or 0)
    balance_now = earnings_now - cost_now
    balance_prev = earnings_prev - cost_prev

    def growth(current, previous):
        if not previous:
            return 100.0 if current else 0.0
        return round(((current - previous) / previous) * 100, 2)

    return JsonResponse(
        {
            "success": True,
            "period": period,
            "kpis": {
                "earnings": {"value": round(earnings_now, 2), "growth": growth(earnings_now, earnings_prev)},
                "orders": {"value": total_orders_now, "growth": growth(total_orders_now, total_orders_prev)},
                "customers": {"value": customers_now, "growth": growth(customers_now, customers_prev)},
                "balance": {"value": round(balance_now, 2), "growth": growth(balance_now, balance_prev)},
            },
        }
    )


@staff_member_required
@require_http_methods(["GET"])
def dashboard_top_products_api(request):
    limit = int(request.GET.get("limit") or 30)
    top_products = (
        OrderItem.objects.values("product_id", "product__name", "product__price", "product__image")
        .annotate(
            order_count=Count("order_id", distinct=True),
            units_sold=Sum("quantity"),
            revenue=Sum(
                ExpressionWrapper(
                    F("quantity") * F("product__price"),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                )
            ),
        )
        .order_by("-units_sold", "-order_count")[:limit]
    )
    product_ids = [p["product_id"] for p in top_products if p.get("product_id")]
    primary_extra_map = {
        img.product_id: img.image.url
        for img in ProductImage.objects.filter(product_id__in=product_ids, is_primary=True)
    }

    def normalized_media_url(raw_value):
        if not raw_value:
            return ""
        if str(raw_value).startswith(("http://", "https://", "/")):
            return str(raw_value)
        return f"{settings.MEDIA_URL}{raw_value}"

    return JsonResponse(
        {
            "success": True,
            "items": [
                {
                    "product_id": p["product_id"],
                    "name": p["product__name"] or "Untitled",
                    "price": float(p["product__price"] or 0),
                    "image_url": (
                        primary_extra_map.get(p["product_id"])
                        or normalized_media_url(p["product__image"])
                    ),
                    "units_sold": int(p["units_sold"] or 0),
                    "order_count": int(p["order_count"] or 0),
                    "revenue": float(p["revenue"] or 0),
                }
                for p in top_products
            ],
        }
    )


@staff_member_required
@require_http_methods(["GET"])
def dashboard_recent_orders_api(request):
    page = int(request.GET.get("page") or 1)
    page_size = int(request.GET.get("page_size") or 8)
    status = (request.GET.get("status") or "").strip().lower()

    qs = Order.objects.select_related("user").order_by("-created_at")
    if status:
        qs = qs.filter(status=status)

    paginator = Paginator(qs, page_size)
    page_obj = paginator.get_page(page)
    items = []
    for order in page_obj.object_list:
        mobile = order.mobile_number
        if not mobile:
            profile = getattr(order.user, "userprofile", None)
            mobile = getattr(profile, "mobile", "") if profile else ""
        items.append(
            {
                "id": order.id,
                "customer_name": (order.user.get_full_name().strip() or order.user.username),
                "email": order.user.email,
                "mobile": mobile or "N/A",
                "address": order.shipping_address or "",
                "total": float(order.total or 0),
                "status": order.status,
                "status_display": order.get_status_display(),
                "created_at": order.created_at.strftime("%Y-%m-%d %H:%M"),
            }
        )

    return JsonResponse(
        {
            "success": True,
            "items": items,
            "pagination": {
                "page": page_obj.number,
                "num_pages": paginator.num_pages,
                "has_previous": page_obj.has_previous(),
                "has_next": page_obj.has_next(),
            },
        }
    )


@staff_member_required
@require_http_methods(["POST"])
def bulk_import_products_api(request):
    csv_file = request.FILES.get("file")
    if not csv_file:
        return JsonResponse({"success": False, "error": "CSV file is required"})
    try:
        decoded = csv_file.read().decode("utf-8")
        reader = csv.DictReader(io.StringIO(decoded))
        created = 0
        for row in reader:
            name = (row.get("name") or "").strip()
            if not name:
                continue
            category_name = (row.get("category") or "General").strip()
            category, _ = Category.objects.get_or_create(name=category_name)
            Product.objects.create(
                name=name,
                description=(row.get("description") or "").strip(),
                price=float(row.get("price") or 0),
                cost_price=float(row.get("cost_price") or 0),
                category=category,
                stock=int(row.get("stock") or 0),
                is_active=str(row.get("is_active") or "1").lower() in ["1", "true", "yes"],
            )
            created += 1
        return JsonResponse({"success": True, "created": created})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


# ─── Simple Product List (for dropdowns) ─────────────────────────────────────

@staff_member_required
@require_http_methods(["GET"])
def product_list_simple_api(request):
    products = Product.objects.filter(is_active=True).order_by('name').values('id', 'name', 'price', 'stock', 'sku')
    return JsonResponse({
        "success": True,
        "products": [
            {
                "id": p["id"],
                "name": p["name"],
                "price": float(p["price"]),
                "stock": p["stock"],
                "sku": p["sku"] or "",
            }
            for p in products
        ],
    })


# ─── Editorial Gallery ────────────────────────────────────────────────────────

@staff_member_required
@require_http_methods(["GET", "POST"])
def editorial_api(request):
    if request.method == "GET":
        items = EditorialMedia.objects.select_related("product").all()
        return JsonResponse({
            "success": True,
            "items": [
                {
                    "id": item.id,
                    "media_type": item.media_type,
                    "file_url": item.file.url,
                    "product_id": item.product_id,
                    "product_name": item.product.name if item.product else "",
                    "product_url": f"/store/product/{item.product_id}/" if item.product_id else "",
                    "order": item.order,
                    "is_active": item.is_active,
                }
                for item in items
            ],
        })

    # POST – create
    try:
        media_type = request.POST.get("media_type", "image")
        file = request.FILES.get("file")
        if not file:
            return JsonResponse({"success": False, "error": "File is required"})
        product_id = request.POST.get("product_id") or None
        if not product_id:
            return JsonResponse({"success": False, "error": "A linked product must be selected"})
        try:
            order = int(request.POST.get("order") or 0)
        except ValueError:
            order = 0
        item = EditorialMedia.objects.create(
            media_type=media_type,
            file=file,
            product_id=product_id,
            order=order,
            is_active=True,
        )
        return JsonResponse({"success": True, "id": item.id})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


@staff_member_required
@require_http_methods(["POST"])
def editorial_update_api(request, item_id):
    item = get_object_or_404(EditorialMedia, id=item_id)
    try:
        if "file" in request.FILES:
            item.file = request.FILES["file"]
        product_id = request.POST.get("product_id") or None
        if not product_id:
            return JsonResponse({"success": False, "error": "A linked product must be selected"})
        item.product_id = product_id
        try:
            item.order = int(request.POST.get("order") or item.order)
        except ValueError:
            pass
        is_active = request.POST.get("is_active")
        if is_active is not None:
            item.is_active = is_active in ["1", "true", "on", "yes"]
        item.save()
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


@staff_member_required
@require_http_methods(["POST"])
def editorial_delete_api(request, item_id):
    item = get_object_or_404(EditorialMedia, id=item_id)
    item.file.delete(save=False)
    item.delete()
    return JsonResponse({"success": True})


@staff_member_required
@require_http_methods(["POST"])
def editorial_toggle_api(request, item_id):
    item = get_object_or_404(EditorialMedia, id=item_id)
    item.is_active = not item.is_active
    item.save(update_fields=["is_active"])
    return JsonResponse({"success": True, "is_active": item.is_active})


@staff_member_required
@require_http_methods(["GET", "POST"])
def collections_api(request):
	if request.method == "GET":
		items = Collection.objects.all().order_by('order', '-created_at')
		return JsonResponse({
			"success": True,
			"collections": [
				{
					"id": c.id,
					"title": c.title,
					"slug": c.slug,
					"order": c.order,
					"is_active": c.is_active,
				}
				for c in items
			],
		})

	try:
		title = (request.POST.get("title") or "").strip()
		slug_raw = (request.POST.get("slug") or "").strip()
		slug = slugify(slug_raw.replace('/', '-').strip())
		if not title or not slug:
			return JsonResponse({"success": False, "error": "Title and slug are required"})
		try:
			order = int(request.POST.get("order") or 0)
		except ValueError:
			order = 0
		is_active = (request.POST.get("is_active") or "on") in ["1", "true", "on", "yes"]
		c = Collection.objects.create(title=title, slug=slug, order=order, is_active=is_active)
		return JsonResponse({"success": True, "id": c.id})
	except Exception as e:
		return JsonResponse({"success": False, "error": str(e)})


@staff_member_required
@require_http_methods(["POST"])
def collections_update_api(request, collection_id):
	c = get_object_or_404(Collection, id=collection_id)
	try:
		title = (request.POST.get("title") or "").strip()
		slug_raw = (request.POST.get("slug") or "").strip()
		slug = slugify(slug_raw.replace('/', '-').strip())
		if title:
			c.title = title
		if slug:
			c.slug = slug
		try:
			c.order = int(request.POST.get("order") or c.order)
		except ValueError:
			pass
		is_active = request.POST.get("is_active")
		if is_active is not None:
			c.is_active = is_active in ["1", "true", "on", "yes"]
		c.save()
		return JsonResponse({"success": True})
	except Exception as e:
		return JsonResponse({"success": False, "error": str(e)})


@staff_member_required
@require_http_methods(["POST"])
def collections_delete_api(request, collection_id):
	c = get_object_or_404(Collection, id=collection_id)
	c.delete()
	return JsonResponse({"success": True})


@staff_member_required
@require_http_methods(["POST"])
def collections_toggle_api(request, collection_id):
	c = get_object_or_404(Collection, id=collection_id)
	c.is_active = not c.is_active
	c.save(update_fields=["is_active"])
	return JsonResponse({"success": True, "is_active": c.is_active})


@staff_member_required
@require_http_methods(["GET", "POST"])
def collection_rows_api(request):
	if request.method == "GET":
		rows = CollectionRow.objects.select_related('collection').prefetch_related('products').all().order_by('order')
		return JsonResponse({
			"success": True,
			"rows": [
				{
					"id": r.id,
					"collection_id": r.collection_id,
					"collection_title": r.collection.title,
					"title": r.title,
					"image_url": r.image.url if r.image else "",
					"image_position": r.image_position,
					"order": r.order,
					"product_ids": list(r.products.values_list('id', flat=True)),
					"product_names": list(r.products.values_list('name', flat=True)),
				}
				for r in rows
			],
		})

	try:
		collection_id = request.POST.get("collection_id")
		if not collection_id:
			return JsonResponse({"success": False, "error": "Collection is required"})
		title = (request.POST.get("title") or "").strip()
		image_position = request.POST.get("image_position") or "left"
		try:
			order = int(request.POST.get("order") or 0)
		except ValueError:
			order = 0
		image = request.FILES.get("image")
		if not image:
			return JsonResponse({"success": False, "error": "Image is required"})
		row = CollectionRow.objects.create(
			collection_id=collection_id,
			title=title,
			image=image,
			image_position=image_position,
			order=order,
		)
		product_ids_raw = (request.POST.get("product_ids") or "").strip()
		if product_ids_raw:
			ids = [int(x) for x in product_ids_raw.split(',') if x.strip().isdigit()]
			row.products.set(Product.objects.filter(id__in=ids))
		return JsonResponse({"success": True, "id": row.id})
	except Exception as e:
		return JsonResponse({"success": False, "error": str(e)})


@staff_member_required
@require_http_methods(["POST"])
def collection_rows_update_api(request, row_id):
	row = get_object_or_404(CollectionRow, id=row_id)
	try:
		collection_id = request.POST.get("collection_id")
		if collection_id:
			row.collection_id = collection_id
		title = request.POST.get("title")
		if title is not None:
			row.title = title
		image_position = request.POST.get("image_position")
		if image_position in ["left", "right"]:
			row.image_position = image_position
		try:
			row.order = int(request.POST.get("order") or row.order)
		except ValueError:
			pass
		if "image" in request.FILES:
			row.image = request.FILES["image"]
		row.save()
		product_ids_raw = request.POST.get("product_ids")
		if product_ids_raw is not None:
			ids = [int(x) for x in (product_ids_raw or "").split(',') if x.strip().isdigit()]
			row.products.set(Product.objects.filter(id__in=ids))
		return JsonResponse({"success": True})
	except Exception as e:
		return JsonResponse({"success": False, "error": str(e)})


@staff_member_required
@require_http_methods(["POST"])
def collection_rows_delete_api(request, row_id):
	row = get_object_or_404(CollectionRow, id=row_id)
	row.image.delete(save=False)
	row.delete()
	return JsonResponse({"success": True})


@staff_member_required
@require_http_methods(["GET", "POST"])
def zoom_carousel_api(request):
	if request.method == "GET":
		items = ZoomCarouselItem.objects.all().order_by('order')
		return JsonResponse({
			"success": True,
			"items": [
				{
					"id": i.id,
					"title": i.title,
					"image_url": i.image.url if i.image else "",
					"link_url": i.link_url,
					"order": i.order,
					"is_active": i.is_active,
				}
				for i in items
			],
		})

	try:
		image = request.FILES.get("image")
		if not image:
			return JsonResponse({"success": False, "error": "Image is required"})
		title = (request.POST.get("title") or "").strip()
		collection_id = (request.POST.get("collection_id") or "").strip()
		link_url = (request.POST.get("link_url") or "").strip()
		if collection_id:
			c = get_object_or_404(Collection, id=collection_id)
			link_url = f"/store/collections/{c.slug}/"
		try:
			order = int(request.POST.get("order") or 0)
		except ValueError:
			order = 0
		is_active = (request.POST.get("is_active") or "on") in ["1", "true", "on", "yes"]
		item = ZoomCarouselItem.objects.create(
			title=title,
			image=image,
			link_url=link_url,
			order=order,
			is_active=is_active,
		)
		return JsonResponse({"success": True, "id": item.id})
	except Exception as e:
		return JsonResponse({"success": False, "error": str(e)})


@staff_member_required
@require_http_methods(["POST"])
def zoom_carousel_update_api(request, item_id):
	item = get_object_or_404(ZoomCarouselItem, id=item_id)
	try:
		title = request.POST.get("title")
		if title is not None:
			item.title = title
		collection_id = request.POST.get("collection_id")
		if collection_id is not None:
			collection_id = str(collection_id).strip()
			if collection_id:
				c = get_object_or_404(Collection, id=collection_id)
				item.link_url = f"/store/collections/{c.slug}/"
			else:
				item.link_url = ""
		link_url = request.POST.get("link_url")
		if link_url is not None and request.POST.get("collection_id") is None:
			item.link_url = link_url
		try:
			item.order = int(request.POST.get("order") or item.order)
		except ValueError:
			pass
		is_active = request.POST.get("is_active")
		if is_active is not None:
			item.is_active = is_active in ["1", "true", "on", "yes"]
		if "image" in request.FILES:
			item.image = request.FILES["image"]
		item.save()
		return JsonResponse({"success": True})
	except Exception as e:
		return JsonResponse({"success": False, "error": str(e)})


@staff_member_required
@require_http_methods(["POST"])
def zoom_carousel_delete_api(request, item_id):
	item = get_object_or_404(ZoomCarouselItem, id=item_id)
	item.image.delete(save=False)
	item.delete()
	return JsonResponse({"success": True})


@staff_member_required
@require_http_methods(["POST"])
def zoom_carousel_toggle_api(request, item_id):
	item = get_object_or_404(ZoomCarouselItem, id=item_id)
	item.is_active = not item.is_active
	item.save(update_fields=["is_active"])
	return JsonResponse({"success": True, "is_active": item.is_active})


# ─── Hero Slides API ────────────────────────────────────────────────────────

@staff_member_required
@require_http_methods(["GET", "POST"])
def hero_slides_api(request):
	if request.method == "GET":
		slides = HeroSlide.objects.all()
		return JsonResponse({
			"success": True,
			"slides": [
				{
					"id": s.id,
					"heading": s.heading,
					"subheading": s.subheading,
					"button_text": s.button_text,
					"button_url": s.button_url,
					"secondary_button_text": s.secondary_button_text,
					"secondary_button_url": s.secondary_button_url,
					"order": s.order,
					"is_active": s.is_active,
					"image_url": s.background_image.url if s.background_image else "",
					"video_url": s.background_video.url if s.background_video else "",
				}
				for s in slides
			],
		})

	try:
		heading = (request.POST.get("heading") or "").strip()
		subheading = (request.POST.get("subheading") or "").strip()
		button_text = (request.POST.get("button_text") or "").strip()
		button_url = (request.POST.get("button_url") or "").strip()
		secondary_button_text = (request.POST.get("secondary_button_text") or "").strip()
		secondary_button_url = (request.POST.get("secondary_button_url") or "").strip()
		try:
			order = int(request.POST.get("order") or 0)
		except ValueError:
			order = 0
		is_active = (request.POST.get("is_active") or "on") in ["1", "true", "on", "yes"]
		slide = HeroSlide.objects.create(
			heading=heading,
			subheading=subheading,
			button_text=button_text,
			button_url=button_url,
			secondary_button_text=secondary_button_text,
			secondary_button_url=secondary_button_url,
			order=order,
			is_active=is_active,
		)
		if "background_image" in request.FILES:
			slide.background_image = request.FILES["background_image"]
		if "background_video" in request.FILES:
			slide.background_video = request.FILES["background_video"]
		slide.save()
		return JsonResponse({"success": True, "id": slide.id})
	except Exception as e:
		return JsonResponse({"success": False, "error": str(e)})


@staff_member_required
@require_http_methods(["POST"])
def hero_slide_update_api(request, slide_id):
	slide = get_object_or_404(HeroSlide, id=slide_id)
	try:
		for field in ("heading", "subheading", "button_text", "button_url",
					  "secondary_button_text", "secondary_button_url"):
			val = request.POST.get(field)
			if val is not None:
				setattr(slide, field, val)
		try:
			slide.order = int(request.POST.get("order") or slide.order)
		except ValueError:
			pass
		is_active = request.POST.get("is_active")
		if is_active is not None:
			slide.is_active = is_active in ["1", "true", "on", "yes"]
		if "background_image" in request.FILES:
			slide.background_image = request.FILES["background_image"]
		if "background_video" in request.FILES:
			slide.background_video = request.FILES["background_video"]
		slide.save()
		return JsonResponse({"success": True})
	except Exception as e:
		return JsonResponse({"success": False, "error": str(e)})


@staff_member_required
@require_http_methods(["POST"])
def hero_slide_delete_api(request, slide_id):
	slide = get_object_or_404(HeroSlide, id=slide_id)
	if slide.background_image:
		slide.background_image.delete(save=False)
	if slide.background_video:
		slide.background_video.delete(save=False)
	slide.delete()
	return JsonResponse({"success": True})


@staff_member_required
@require_http_methods(["POST"])
def hero_slide_toggle_api(request, slide_id):
	slide = get_object_or_404(HeroSlide, id=slide_id)
	slide.is_active = not slide.is_active
	slide.save(update_fields=["is_active"])
	return JsonResponse({"success": True, "is_active": slide.is_active})


# ─── Site Settings API ───────────────────────────────────────────────────────

@staff_member_required
@require_http_methods(["GET", "POST"])
def site_settings_api(request):
	settings_obj = SiteSettings.get_settings()
	if request.method == "GET":
		return JsonResponse({
			"success": True,
			"glass_flash_enabled": settings_obj.glass_flash_enabled,
			"shipping_charge": float(settings_obj.shipping_charge),
			"free_shipping_above": float(settings_obj.free_shipping_above),
			"cod_fee": float(settings_obj.cod_fee),
			"return_exchange_fee": float(settings_obj.return_exchange_fee),
			"shipping_charge": float(settings_obj.shipping_charge),
			"free_shipping_above": float(settings_obj.free_shipping_above),
			"razorpay_key_id": settings_obj.razorpay_key_id,
			"razorpay_has_secret": bool(settings_obj.razorpay_key_secret),
			# Never expose the secret to the frontend
		})
	try:
		data = json.loads(request.body)
		if "glass_flash_enabled" in data:
			settings_obj.glass_flash_enabled = bool(data["glass_flash_enabled"])
		if "shipping_charge" in data:
			settings_obj.shipping_charge = data["shipping_charge"]
		if "free_shipping_above" in data:
			settings_obj.free_shipping_above = data["free_shipping_above"]
		if "cod_fee" in data:
			settings_obj.cod_fee = data["cod_fee"]
		if "return_exchange_fee" in data:
			settings_obj.return_exchange_fee = data["return_exchange_fee"]
		if "razorpay_key_id" in data:
			settings_obj.razorpay_key_id = data["razorpay_key_id"]
		if "razorpay_key_secret" in data and data["razorpay_key_secret"]:
			settings_obj.razorpay_key_secret = data["razorpay_key_secret"]
		settings_obj.save()
		return JsonResponse({
			"success": True,
			"settings": {
				"cod_fee": float(settings_obj.cod_fee),
				"return_exchange_fee": float(settings_obj.return_exchange_fee),
				"shipping_charge": float(settings_obj.shipping_charge),
				"free_shipping_above": float(settings_obj.free_shipping_above),
				"razorpay_key_id": settings_obj.razorpay_key_id,
				"razorpay_has_secret": bool(settings_obj.razorpay_key_secret),
			}
		})
	except Exception as e:
		return JsonResponse({"success": False, "error": str(e)})


# ─── Coupon CRUD ──────────────────────────────────────────────────────────────

@staff_member_required
@require_http_methods(["GET", "POST"])
def coupons_api(request):
	if request.method == "GET":
		coupons = list(Coupon.objects.all().order_by('-id').values(
			'id', 'code', 'description', 'discount_type', 'discount_value',
			'min_cart_amount', 'max_discount', 'is_active',
			'valid_from', 'valid_to', 'usage_limit', 'usage_count',
		))
		for c in coupons:
			c['valid_from'] = c['valid_from'].strftime('%Y-%m-%dT%H:%M') if c['valid_from'] else ''
			c['valid_to'] = c['valid_to'].strftime('%Y-%m-%dT%H:%M') if c['valid_to'] else ''
			c['discount_value'] = float(c['discount_value'])
			c['min_cart_amount'] = float(c['min_cart_amount'])
			c['max_discount'] = float(c['max_discount']) if c['max_discount'] is not None else None
		return JsonResponse({"success": True, "coupons": coupons})
	try:
		data = json.loads(request.body)
		coupon = Coupon.objects.create(
			code=data['code'].strip().upper(),
			description=data.get('description', ''),
			discount_type=data.get('discount_type', 'percent'),
			discount_value=data['discount_value'],
			min_cart_amount=data.get('min_cart_amount', 0),
			max_discount=data.get('max_discount') or None,
			is_active=data.get('is_active', True),
			valid_from=data.get('valid_from') or None,
			valid_to=data.get('valid_to') or None,
			usage_limit=data.get('usage_limit') or None,
		)
		return JsonResponse({"success": True, "id": coupon.id})
	except Exception as e:
		return JsonResponse({"success": False, "error": str(e)})


@staff_member_required
@require_http_methods(["POST"])
def coupon_update_api(request, coupon_id):
	coupon = get_object_or_404(Coupon, pk=coupon_id)
	try:
		data = json.loads(request.body)
		for field in ('code', 'description', 'discount_type', 'discount_value',
		              'min_cart_amount', 'is_active'):
			if field in data:
				setattr(coupon, field, data[field])
		if 'code' in data:
			coupon.code = data['code'].strip().upper()
		coupon.max_discount = data.get('max_discount') or None
		coupon.valid_from = data.get('valid_from') or None
		coupon.valid_to = data.get('valid_to') or None
		coupon.usage_limit = data.get('usage_limit') or None
		coupon.save()
		return JsonResponse({"success": True})
	except Exception as e:
		return JsonResponse({"success": False, "error": str(e)})


@staff_member_required
@require_http_methods(["POST"])
def coupon_delete_api(request, coupon_id):
	coupon = get_object_or_404(Coupon, pk=coupon_id)
	coupon.delete()
	return JsonResponse({"success": True})


@staff_member_required
@require_http_methods(["POST"])
def coupon_toggle_api(request, coupon_id):
	coupon = get_object_or_404(Coupon, pk=coupon_id)
	coupon.is_active = not coupon.is_active
	coupon.save()
	return JsonResponse({"success": True, "is_active": coupon.is_active})


# ══════════════════════════════════════════════════════════════════════════════
# CUSTOMER ANALYTICS & MANAGEMENT APIs
# ══════════════════════════════════════════════════════════════════════════════

def _get_or_create_customer_profile(user):
	profile, _ = CustomerProfile.objects.get_or_create(user=user)
	return profile


@staff_member_required
def customer_list_api(request):
	users = (
		User.objects.filter(is_staff=False)
		.select_related('userprofile', 'customer_profile')
		.annotate(
			order_count=Count('order', distinct=True),
			lifetime_val=Sum('order__total', filter=Q(order__status='delivered')),
		)
		.order_by('-date_joined')
	)
	data = []
	for u in users:
		cp = getattr(u, 'customer_profile', None)
		if cp is None:
			cp = _get_or_create_customer_profile(u)
		phone = ''
		try:
			phone = u.userprofile.mobile or u.userprofile.phone or cp.alternate_phone
		except Exception:
			pass
		data.append({
			'id': u.id,
			'customer_id': cp.customer_id,
			'name': u.get_full_name() or u.username,
			'email': u.email,
			'phone': phone,
			'is_enabled': cp.is_enabled,
			'is_active': u.is_active,
			'total_orders': u.order_count or 0,
			'lifetime_value': float(u.lifetime_val or 0),
			'join_date': u.date_joined.strftime('%Y-%m-%d'),
			'notes': cp.notes,
		})
	return JsonResponse({'success': True, 'customers': data})


@staff_member_required
def customer_orders_api(request, customer_id):
	user = get_object_or_404(User, id=customer_id)
	orders = Order.objects.filter(user=user).order_by('-created_at')
	return JsonResponse({
		'success': True,
		'orders': [{
			'id': o.id,
			'total': float(o.total),
			'status': o.status,
			'status_display': o.get_status_display(),
			'created_at': o.created_at.strftime('%d %b %Y, %H:%M'),
			'items_count': o.items.count(),
		} for o in orders],
	})


@staff_member_required
def customer_create_api(request):
	if request.method != 'POST':
		return JsonResponse({'success': False, 'error': 'POST required'})
	try:
		data = json.loads(request.body)
		email = data.get('email', '').strip()
		if not email:
			return JsonResponse({'success': False, 'error': 'Email required'})
		if User.objects.filter(email=email).exists():
			return JsonResponse({'success': False, 'error': 'Email already registered'})
		import random, string
		temp_pw = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
		u = User.objects.create_user(
			username=email,
			email=email,
			password=temp_pw,
			first_name=data.get('first_name', '').strip(),
			last_name=data.get('last_name', '').strip(),
		)
		cp = _get_or_create_customer_profile(u)
		cp.alternate_phone = data.get('alternate_phone', '')
		cp.gstin = data.get('gstin', '')
		cp.notes = data.get('notes', '')
		cp.is_enabled = data.get('is_enabled', True)
		cp.save()
		return JsonResponse({'success': True, 'customer_id': cp.customer_id})
	except Exception as e:
		return JsonResponse({'success': False, 'error': str(e)})


@staff_member_required
def customer_update_api(request, customer_id):
	if request.method != 'POST':
		return JsonResponse({'success': False, 'error': 'POST required'})
	try:
		user = get_object_or_404(User, id=customer_id)
		data = json.loads(request.body)
		user.first_name = data.get('first_name', user.first_name)
		user.last_name  = data.get('last_name',  user.last_name)
		user.email      = data.get('email',       user.email)
		user.save()
		cp = _get_or_create_customer_profile(user)
		cp.alternate_phone = data.get('alternate_phone', cp.alternate_phone)
		cp.gstin  = data.get('gstin',  cp.gstin)
		cp.notes  = data.get('notes',  cp.notes)
		if 'is_enabled' in data:
			cp.is_enabled = bool(data['is_enabled'])
		cp.save()
		# also update phone in UserProfile if present
		try:
			if data.get('phone'):
				user.userprofile.mobile = data['phone']
				user.userprofile.save(update_fields=['mobile'])
		except Exception:
			pass
		return JsonResponse({'success': True})
	except Exception as e:
		return JsonResponse({'success': False, 'error': str(e)})


@staff_member_required
def customer_toggle_api(request, customer_id):
	user = get_object_or_404(User, id=customer_id)
	cp = _get_or_create_customer_profile(user)
	cp.is_enabled = not cp.is_enabled
	cp.save(update_fields=['is_enabled'])
	return JsonResponse({'success': True, 'is_enabled': cp.is_enabled})


@staff_member_required
def customer_category_graph_api(request):
	rows = (
		OrderItem.objects
		.filter(order__status='delivered')
		.values('order__user__id', 'product__category__name')
		.annotate(total_spent=Sum('price'))
		.order_by('order__user__id')
	)
	customers_map = {}
	for row in rows:
		uid = row['order__user__id']
		cat = row['product__category__name'] or 'Uncategorized'
		if uid not in customers_map:
			try:
				u = User.objects.get(pk=uid)
				cp = getattr(u, 'customer_profile', None)
				label = (cp.customer_id if cp else None) or (u.get_full_name() or u.username)[:10]
			except Exception:
				label = f'#{uid}'
			customers_map[uid] = {'label': label, 'categories': {}}
		customers_map[uid]['categories'][cat] = float(row['total_spent'])
	# Return top 15 customers by total spend
	result = sorted(
		customers_map.values(),
		key=lambda x: sum(x['categories'].values()),
		reverse=True
	)[:15]
	return JsonResponse({'success': True, 'data': result})


@staff_member_required
def top_customers_api(request):
	days = int(request.GET.get('days', 30))
	since = timezone.now() - timedelta(days=days)
	qs = (
		User.objects
		.filter(order__status='delivered', order__created_at__gte=since)
		.annotate(total_spent=Sum('order__total'))
		.select_related('customer_profile')
		.order_by('-total_spent')[:20]
	)
	data = []
	for u in qs:
		cp = getattr(u, 'customer_profile', None)
		if cp is None:
			cp = _get_or_create_customer_profile(u)
		data.append({
			'id': u.id,
			'customer_id': cp.customer_id,
			'name': u.get_full_name() or u.username,
			'email': u.email,
			'total_spent': float(u.total_spent or 0),
		})
	return JsonResponse({'success': True, 'customers': data})

# ──────────────────────────────────────────────────────────────────────────────
#  ORDER MANAGEMENT UPGRADE  –  Manual Order, Edit Items, Kanban, Trend, Search
# ──────────────────────────────────────────────────────────────────────────────

@staff_member_required
@require_http_methods(["GET"])
def customer_search_api(request):
    """Search users by name / email / phone for manual order creation."""
    q = (request.GET.get("q") or "").strip()
    if len(q) < 2:
        return JsonResponse({"success": True, "customers": []})
    users = User.objects.filter(
        Q(email__icontains=q) |
        Q(first_name__icontains=q) |
        Q(last_name__icontains=q) |
        Q(username__icontains=q) |
        Q(userprofile__mobile__icontains=q)
    ).distinct()[:10]
    customers = []
    for u in users:
        try:
            phone = u.userprofile.mobile or ""
        except Exception:
            phone = ""
        customers.append({
            "id": u.id,
            "name": u.get_full_name() or u.username,
            "email": u.email,
            "phone": phone,
        })
    return JsonResponse({"success": True, "customers": customers})


@staff_member_required
@require_http_methods(["POST"])
def create_manual_order_api(request):
    """Create a manual order on behalf of a customer."""
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    user_id = data.get("user_id")
    if not user_id:
        return JsonResponse({"success": False, "error": "Customer required"}, status=400)
    user = get_object_or_404(User, id=user_id)

    items_data = data.get("items", [])
    if not items_data:
        return JsonResponse({"success": False, "error": "At least one product required"}, status=400)

    shipping_address = (data.get("shipping_address") or "").strip()
    if not shipping_address:
        return JsonResponse({"success": False, "error": "Shipping address required"}, status=400)

    payment_method = data.get("payment_method", "cod")
    admin_notes = data.get("reason", "")

    # Calculate subtotal
    subtotal = 0
    order_items = []
    for item_data in items_data:
        product_id = item_data.get("product_id")
        qty = int(item_data.get("quantity", 1))
        custom_price = item_data.get("price")
        if not product_id:
            continue
        product = get_object_or_404(Product, id=product_id)
        price = float(custom_price) if custom_price else float(product.price)
        subtotal += price * qty
        order_items.append({"product": product, "quantity": qty, "price": price})

    if not order_items:
        return JsonResponse({"success": False, "error": "No valid products"}, status=400)

    # Add COD fee if applicable (use frontend-sent value or fall back to SiteSettings)
    cod_fee_amount = 0.0
    if payment_method == "cod":
        frontend_cod_fee = data.get("cod_fee")
        if frontend_cod_fee is not None:
            cod_fee_amount = float(frontend_cod_fee)
        else:
            site_settings = SiteSettings.get_settings()
            cod_fee_amount = float(site_settings.cod_fee)
    total = subtotal + cod_fee_amount

    order = Order.objects.create(
        user=user,
        shipping_address=shipping_address,
        shipping_name=user.get_full_name() or user.username,
        total=total,
        payment_method=payment_method,
        payment_status="pending",
        status="pending",
        admin_notes=admin_notes,
        is_manual=True,
        cod_fee_amount=cod_fee_amount,
    )
    for oi in order_items:
        OrderItem.objects.create(
            order=order,
            product=oi["product"],
            quantity=oi["quantity"],
            price=oi["price"],
        )

    # User-facing notification
    UserNotification.objects.create(
        user=user,
        title="New Order Created",
        message=f"Order #{order.id} has been placed for you. Total: ₹{total:.2f}",
        notif_type="manual_order",
        related_order=order,
    )
    return JsonResponse({"success": True, "order_id": order.id})


@staff_member_required
@require_http_methods(["GET"])
def order_edit_items_api(request, order_id):
    """Return items in an order for the edit modal."""
    order = get_object_or_404(Order, id=order_id)
    items = []
    for item in order.items.select_related("product").all():
        img_url = None
        try:
            img_url = item.product.image.url if item.product.image else None
        except Exception:
            pass
        items.append({
            "id": item.id,
            "product_id": item.product.id,
            "product_name": item.product.name,
            "sku": item.product.sku or "",
            "image_url": img_url,
            "quantity": item.quantity,
            "price": float(item.price),
            "original_price": float(item.product.price),
        })
    return JsonResponse({
        "success": True,
        "order_id": order.id,
        "customer": order.user.get_full_name() or order.user.username,
        "status": order.status,
        "items": items,
    })


@staff_member_required
@require_http_methods(["POST"])
def order_update_items_api(request, order_id):
    """Update items in an existing order (product, qty, price)."""
    order = get_object_or_404(Order, id=order_id)
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    items_data = data.get("items", [])
    reason = data.get("reason", "Admin edit")
    changes = []

    for item_data in items_data:
        item_id = item_data.get("item_id")
        new_product_id = item_data.get("product_id")
        new_qty = int(item_data.get("quantity", 1))
        new_price = item_data.get("price")

        try:
            item = OrderItem.objects.get(id=item_id, order=order)
        except OrderItem.DoesNotExist:
            continue

        old_name = item.product.name
        if new_product_id and new_product_id != item.product_id:
            new_product = get_object_or_404(Product, id=new_product_id)
            item.product = new_product
            changes.append(f"Product changed from {old_name} to {new_product.name}")
        if new_price is not None:
            item.price = float(new_price)
        if new_qty != item.quantity:
            item.quantity = new_qty
        item.save()

    # Recalculate order total
    new_total = sum(i.price * i.quantity for i in order.items.all())
    order.total = new_total
    if reason:
        order.admin_notes = (order.admin_notes + "\n" + reason).strip()
    order.save(update_fields=["total", "admin_notes"])

    # Notify user
    UserNotification.objects.create(
        user=order.user,
        title=f"Order #{order.id} Updated",
        message=f"Your order has been updated by admin. New total: ₹{float(new_total):.2f}. " + (", ".join(changes) or "Items updated."),
        notif_type="order_updated",
        related_order=order,
    )
    return JsonResponse({"success": True, "new_total": float(new_total)})


@staff_member_required
@require_http_methods(["GET"])
def orders_kanban_api(request):
    """Return orders grouped by status for the kanban board, with filters."""
    status_filter = request.GET.get("status", "")
    payment_filter = request.GET.get("payment", "")
    date_range = request.GET.get("date_range", "all")
    search = (request.GET.get("search") or "").strip()

    orders_qs = Order.objects.select_related("user").order_by("-created_at")

    if date_range == "today":
        orders_qs = orders_qs.filter(created_at__date=timezone.now().date())
    elif date_range == "week":
        orders_qs = orders_qs.filter(created_at__gte=timezone.now() - timedelta(days=7))
    elif date_range == "month":
        orders_qs = orders_qs.filter(created_at__gte=timezone.now() - timedelta(days=30))

    if status_filter and status_filter != "all":
        orders_qs = orders_qs.filter(status=status_filter)
    if payment_filter and payment_filter != "all":
        orders_qs = orders_qs.filter(payment_method=payment_filter)
    if search:
        orders_qs = orders_qs.filter(
            Q(id__icontains=search) |
            Q(user__email__icontains=search) |
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(mobile_number__icontains=search)
        )

    # Limit to last 200 orders total for kanban
    orders_qs = orders_qs[:200]

    grouped = {}
    status_order = ['pending','processing','packed','shipped','out_for_delivery','delivered','rto','returned','refund_pending','refund_completed','cancelled']
    for s in status_order:
        grouped[s] = []

    for order in orders_qs:
        name = order.user.get_full_name() or order.user.username
        s = order.status if order.status in grouped else 'pending'
        grouped[s].append({
            "id": order.id,
            "customer": name,
            "email": order.user.email,
            "phone": order.mobile_number or "",
            "total": float(order.total),
            "payment_method": order.payment_method,
            "payment_status": order.payment_status,
            "status": order.status,
            "status_display": order.get_status_display(),
            "date": order.created_at.strftime("%b %d, %H:%M"),
            "is_manual": order.is_manual,
            "address": order.shipping_address[:50] if order.shipping_address else "",
        })

    # Status counts for funnel/summary
    all_orders_qs = Order.objects.all()
    summary = {s: all_orders_qs.filter(status=s).count() for s in status_order}
    summary["total"] = all_orders_qs.count()

    return JsonResponse({"success": True, "orders": grouped, "summary": summary})


@staff_member_required
@require_http_methods(["GET"])
def orders_trend_api(request):
    """Daily order counts for the past N days (for trend line chart)."""
    days = int(request.GET.get("days", 30))
    today = timezone.now().date()
    start = today - timedelta(days=days - 1)

    qs = (
        Order.objects.filter(created_at__date__gte=start)
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(
            total_orders=Count("id"),
            delivered=Count("id", filter=Q(status="delivered")),
            cancelled=Count("id", filter=Q(status="cancelled")),
        )
        .order_by("day")
    )
    by_day = {row["day"]: row for row in qs}

    labels, total_list, delivered_list, cancelled_list = [], [], [], []
    current = start
    while current <= today:
        labels.append(current.strftime("%b %d"))
        row = by_day.get(current, {})
        total_list.append(row.get("total_orders", 0))
        delivered_list.append(row.get("delivered", 0))
        cancelled_list.append(row.get("cancelled", 0))
        current += timedelta(days=1)

    return JsonResponse({
        "success": True,
        "labels": labels,
        "total": total_list,
        "delivered": delivered_list,
        "cancelled": cancelled_list,
    })


@staff_member_required
@require_http_methods(["GET"])
def lifecycle_analytics_api(request):
    """Return lifecycle hub analytics: stage counts, conversion rates, avg times, aging."""
    now = timezone.now()

    # Stage counts
    stage_counts = dict(
        Order.objects.values("status").annotate(c=Count("id")).values_list("status", "c")
    )

    pipeline_statuses = ["pending", "processing", "packed", "shipped", "out_for_delivery"]
    active_pipeline = sum(stage_counts.get(s, 0) for s in pipeline_statuses)
    completed = stage_counts.get("delivered", 0)
    cancelled = stage_counts.get("cancelled", 0)
    returned = stage_counts.get("returned", 0) + stage_counts.get("rto", 0)
    total_all = Order.objects.count()

    # Conversion rates (funnel: placed → processing → packed → shipped → delivered)
    placed = total_all or 1  # avoid division by zero
    confirmed_rate = round((stage_counts.get("processing", 0) + sum(stage_counts.get(s, 0) for s in ["packed", "shipped", "out_for_delivery", "delivered"])) / placed * 100, 1)
    packing_rate   = round((stage_counts.get("packed", 0)     + sum(stage_counts.get(s, 0) for s in ["shipped", "out_for_delivery", "delivered"])) / placed * 100, 1)
    shipping_rate  = round((stage_counts.get("shipped", 0)    + stage_counts.get("out_for_delivery", 0) + stage_counts.get("delivered", 0)) / placed * 100, 1)
    delivery_rate  = round(stage_counts.get("delivered", 0)   / placed * 100, 1)

    # Funnel data for chart (absolute counts at each stage or past it)
    funnel = [
        {"stage": "Placed",     "count": total_all},
        {"stage": "Confirmed",  "count": total_all - stage_counts.get("pending", 0)},
        {"stage": "Packed",     "count": sum(stage_counts.get(s, 0) for s in ["packed", "shipped", "out_for_delivery", "delivered", "rto", "returned"])},
        {"stage": "Shipped",    "count": sum(stage_counts.get(s, 0) for s in ["shipped", "out_for_delivery", "delivered", "rto"])},
        {"stage": "Delivered",  "count": stage_counts.get("delivered", 0)},
    ]

    # Avg transition times using timestamp fields (in hours, rounded to 1 dp)
    def avg_hours_between(field_a, field_b):
        """Average hours between two datetime fields on Order."""
        qs = Order.objects.filter(
            **{f"{field_a}__isnull": False, f"{field_b}__isnull": False}
        )
        total_secs = 0
        count = 0
        for o in qs.only(field_a, field_b)[:2000]:  # cap for perf
            a = getattr(o, field_a)
            b = getattr(o, field_b)
            if b > a:
                total_secs += (b - a).total_seconds()
                count += 1
        return round(total_secs / count / 3600, 1) if count else 0

    speed = [
        {"label": "Placed → Confirmed", "hours": None},  # no packed_at baseline for this
        {"label": "Confirmed → Packed",  "hours": None},
        {"label": "Packed → Shipped",    "hours": avg_hours_between("packed_at", "shipped_at")},
        {"label": "Shipped → Delivered", "hours": avg_hours_between("shipped_at", "delivered_at")},
    ]

    # Placed → Packed using created_at → packed_at
    qs_p2p = Order.objects.filter(packed_at__isnull=False)
    total_secs_p2p = 0
    cnt_p2p = 0
    for o in qs_p2p.only("created_at", "packed_at")[:2000]:
        if o.packed_at > o.created_at:
            total_secs_p2p += (o.packed_at - o.created_at).total_seconds()
            cnt_p2p += 1
    speed[0]["hours"] = round(total_secs_p2p / cnt_p2p / 3600, 1) if cnt_p2p else 0
    speed[0]["label"] = "Placed → Packed"

    # Packed → Shipped already done above, shift the labels
    speed[1]["label"] = "Packed → Shipped"
    speed[1]["hours"] = speed[2]["hours"]
    speed[2]["label"] = "Shipped → OFD"
    speed[2]["hours"] = avg_hours_between("shipped_at", "out_for_delivery_at")
    speed[3]["label"] = "OFD → Delivered"
    speed[3]["hours"] = avg_hours_between("out_for_delivery_at", "delivered_at")

    # Order aging: orders stuck in early stages
    active_qs = Order.objects.filter(status__in=["pending", "processing"])
    aging_24  = active_qs.filter(created_at__lt=now - timedelta(hours=24)).count()
    aging_48  = active_qs.filter(created_at__lt=now - timedelta(hours=48)).count()
    aging_72  = active_qs.filter(created_at__lt=now - timedelta(hours=72)).count()

    # Recent orders per stage for quick view (latest 5 per pipeline stage)
    stage_orders = {}
    for st in pipeline_statuses:
        orders = Order.objects.filter(status=st).order_by("-created_at")[:5]
        stage_orders[st] = [
            {
                "id": o.id,
                "customer": o.shipping_name or (o.user.get_full_name() or o.user.username),
                "total": float(o.total),
                "created_at": o.created_at.strftime("%b %d, %H:%M"),
                "hours_ago": round((now - o.created_at).total_seconds() / 3600, 1),
            }
            for o in orders
        ]

    return JsonResponse({
        "success": True,
        "total_orders": total_all,
        "active_pipeline": active_pipeline,
        "completed": completed,
        "cancelled": cancelled,
        "returned": returned,
        "stage_counts": stage_counts,
        "funnel": funnel,
        "speed": speed,
        "aging": {"gt24": aging_24, "gt48": aging_48, "gt72": aging_72},
        "conversion": {
            "confirmed": confirmed_rate,
            "packing": packing_rate,
            "shipping": shipping_rate,
            "delivery": delivery_rate,
        },
        "stage_orders": stage_orders,
    })


@staff_member_required
@require_http_methods(["POST"])
def admin_cancel_order_api(request, order_id):
    """Admin cancels an order with a mandatory reason. Notifies the customer."""
    order = get_object_or_404(Order, id=order_id)

    # Guard: don't allow re-cancelling or cancelling already-closed orders
    NON_CANCELLABLE = ["cancelled", "refund_completed"]
    if order.status in NON_CANCELLABLE:
        return JsonResponse(
            {"success": False, "error": f"Order is already '{order.status}' and cannot be cancelled."},
            status=400,
        )

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    reason_code = data.get("reason_code", "other")
    reason_note = (data.get("reason_note") or "").strip()

    REASON_LABELS = {
        "out_of_stock":      "Item(s) out of stock",
        "customer_request":  "Customer requested cancellation",
        "payment_issue":     "Payment issue / not received",
        "wrong_address":     "Wrong / undeliverable address",
        "fraud":             "Suspicious / fraudulent order",
        "duplicate":         "Duplicate order",
        "other":             "Other reason",
    }
    reason_label = REASON_LABELS.get(reason_code, reason_code)
    full_reason = reason_label + (f" — {reason_note}" if reason_note else "")

    prev_status = order.status
    order.status = "cancelled"
    order.admin_notes = (order.admin_notes + "\n" if order.admin_notes else "") + f"[Admin Cancel] {full_reason}"
    order.save(update_fields=["status", "admin_notes", "updated_at"])

    # Lifecycle log
    from .models import OrderLifecycleLog
    OrderLifecycleLog.objects.create(
        order=order,
        event_type="status_change",
        previous_status=prev_status,
        new_status="cancelled",
        note=f"Admin cancelled: {full_reason}",
        created_by=request.user,
    )

    # Notify customer
    UserNotification.objects.create(
        user=order.user,
        title=f"Order #{order.id} Cancelled",
        message=f"Your order #{order.id} has been cancelled by admin. Reason: {full_reason}. "
                f"If you have any questions please contact support.",
        notif_type="order_cancelled",
        related_order=order,
    )

    return JsonResponse({
        "success": True,
        "message": f"Order #{order.id} cancelled.",
        "order_id": order.id,
    })


# ─────────────────────────────────────────────
#  USER MANAGEMENT  (superuser-only)
# ─────────────────────────────────────────────

def _serialize_admin_user(u):
    """Return a dict representation of a staff User + AdminUserProfile."""
    try:
        profile = u.admin_profile
        designation   = profile.designation
        phone_number  = profile.phone_number
        address       = profile.address
        features      = profile.assigned_features or []
    except AdminUserProfile.DoesNotExist:
        designation = phone_number = address = ""
        features = []
    return {
        "id":               u.id,
        "username":         u.username,
        "email":            u.email,
        "first_name":       u.first_name,
        "last_name":        u.last_name,
        "full_name":        u.get_full_name() or u.username,
        "designation":      designation,
        "phone_number":     phone_number,
        "address":          address,
        "assigned_features": features,
        "is_active":        u.is_active,
        "is_superuser":     u.is_superuser,
        "date_joined":      u.date_joined.strftime("%b %d, %Y"),
        "last_login":       u.last_login.strftime("%b %d, %Y %H:%M") if u.last_login else "Never",
    }


@staff_member_required
@require_http_methods(["GET"])
def admin_users_list_api(request):
    if not request.user.is_superuser:
        return JsonResponse({"success": False, "error": "Permission denied."}, status=403)
    users = User.objects.filter(is_staff=True).select_related("admin_profile").order_by("-date_joined")
    return JsonResponse({"success": True, "users": [_serialize_admin_user(u) for u in users]})


@staff_member_required
@require_http_methods(["POST"])
def admin_users_create_api(request):
    if not request.user.is_superuser:
        return JsonResponse({"success": False, "error": "Permission denied."}, status=403)
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    email       = (data.get("email") or "").strip()
    first_name  = (data.get("first_name") or "").strip()
    last_name   = (data.get("last_name") or "").strip()
    password    = (data.get("password") or "").strip()
    designation = (data.get("designation") or "").strip()
    phone       = (data.get("phone_number") or "").strip()
    address     = (data.get("address") or "").strip()
    features    = data.get("assigned_features", [])
    # username = email prefix unless explicitly supplied
    username    = (data.get("username") or email.split("@")[0]).strip()

    if not email:
        return JsonResponse({"success": False, "error": "Email is required."}, status=400)
    if not password or len(password) < 6:
        return JsonResponse({"success": False, "error": "Password must be at least 6 characters."}, status=400)
    if User.objects.filter(username=username).exists():
        return JsonResponse({"success": False, "error": f"Username '{username}' is already taken."}, status=400)
    if User.objects.filter(email__iexact=email).exists():
        return JsonResponse({"success": False, "error": f"Email '{email}' is already in use."}, status=400)

    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        is_staff=True,
        is_active=True,
    )
    AdminUserProfile.objects.create(
        user=user,
        designation=designation,
        phone_number=phone,
        address=address,
        assigned_features=features,
    )
    return JsonResponse({"success": True, "message": f"User '{username}' created.", "user": _serialize_admin_user(user)})


@staff_member_required
@require_http_methods(["POST"])
def admin_users_update_api(request, user_id):
    if not request.user.is_superuser:
        return JsonResponse({"success": False, "error": "Permission denied."}, status=403)
    user = get_object_or_404(User, id=user_id, is_staff=True)
    if user.is_superuser and user.id != request.user.id:
        return JsonResponse({"success": False, "error": "Cannot modify another superuser."}, status=400)
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    user.first_name = (data.get("first_name") or user.first_name).strip()
    user.last_name  = (data.get("last_name")  or user.last_name).strip()
    new_email       = (data.get("email") or "").strip()
    if new_email and new_email.lower() != user.email.lower():
        if User.objects.filter(email__iexact=new_email).exclude(id=user.id).exists():
            return JsonResponse({"success": False, "error": "Email already in use."}, status=400)
        user.email = new_email
    new_pw = (data.get("password") or "").strip()
    if new_pw:
        if len(new_pw) < 6:
            return JsonResponse({"success": False, "error": "Password must be at least 6 characters."}, status=400)
        user.set_password(new_pw)
    user.save()

    profile, _ = AdminUserProfile.objects.get_or_create(user=user)
    profile.designation   = (data.get("designation")   or profile.designation).strip()
    profile.phone_number  = (data.get("phone_number")  or profile.phone_number).strip()
    profile.address       = (data.get("address")       or profile.address).strip()
    if "assigned_features" in data:
        profile.assigned_features = data["assigned_features"]
    profile.save()
    return JsonResponse({"success": True, "message": f"User '{user.username}' updated.", "user": _serialize_admin_user(user)})


@staff_member_required
@require_http_methods(["POST"])
def admin_users_toggle_api(request, user_id):
    if not request.user.is_superuser:
        return JsonResponse({"success": False, "error": "Permission denied."}, status=403)
    user = get_object_or_404(User, id=user_id, is_staff=True)
    if user.id == request.user.id:
        return JsonResponse({"success": False, "error": "Cannot deactivate your own account."}, status=400)
    if user.is_superuser:
        return JsonResponse({"success": False, "error": "Cannot toggle a superuser."}, status=400)
    user.is_active = not user.is_active
    user.save(update_fields=["is_active"])
    return JsonResponse({"success": True, "is_active": user.is_active,
                         "message": f"User {'activated' if user.is_active else 'deactivated'}."})


@staff_member_required
@require_http_methods(["POST"])
def admin_users_delete_api(request, user_id):
    if not request.user.is_superuser:
        return JsonResponse({"success": False, "error": "Permission denied."}, status=403)
    user = get_object_or_404(User, id=user_id, is_staff=True)
    if user.id == request.user.id:
        return JsonResponse({"success": False, "error": "Cannot delete your own account."}, status=400)
    if user.is_superuser:
        return JsonResponse({"success": False, "error": "Cannot delete a superuser here."}, status=400)
    uname = user.username
    user.delete()
    return JsonResponse({"success": True, "message": f"User '{uname}' deleted."})


# ══════════════════════════════════════════════════════════════
#  RETURN & REFUND MANAGEMENT  APIs
# ══════════════════════════════════════════════════════════════

def _serialize_return(rr):
    """Compact serialization for list/kanban views."""
    from django.utils import timezone as tz
    age = (tz.now() - rr.created_at).days
    return {
        "id":           rr.id,
        "rtn_id":       f"RTN-{rr.id:04d}",
        "order_id":     rr.order_id,
        "customer_id":  rr.customer_id,
        "customer_name": rr.customer.get_full_name() or rr.customer.username,
        "customer_email": rr.customer.email,
        "product_name": rr.product_name,
        "product_sku":  rr.product_sku,
        "order_amount": float(rr.order_amount),
        "quantity":     rr.quantity,
        "return_reason": rr.return_reason,
        "reason_label": rr.get_return_reason_display(),
        "status":       rr.status,
        "priority":     rr.priority,
        "qc_result":    rr.qc_result,
        "resale_status":rr.resale_status,
        "final_refund_amount": float(rr.final_refund_amount) if rr.final_refund_amount is not None else None,
        "calculated_refund": rr.calculated_refund,
        "is_high_value": rr.is_high_value,
        "age_days":     age,
        "created_at":   rr.created_at.strftime("%b %d, %Y"),
        "created_iso":  rr.created_at.isoformat(),
        "refunded_at":  rr.refunded_at.strftime("%b %d, %Y") if rr.refunded_at else None,
    }


def _serialize_return_detail(rr):
    """Full serialization for the investigation drawer."""
    base = _serialize_return(rr)
    # Refund method + bank details
    base.update({
        "refund_method":       rr.refund_method,
        "account_holder_name": rr.account_holder_name,
        "account_number":      rr.account_number,
        "ifsc_code":           rr.ifsc_code,
        "bank_name":           rr.bank_name,
        "order_payment_method": rr.order.payment_method if rr.order else "",
    })
    base.update({
        "reason_detail":       rr.reason_detail,
        "return_images":       rr.return_images,
        "admin_notes":         rr.admin_notes,
        "refund_reference":    rr.refund_reference,
        "shipping_deduction":  float(rr.shipping_deduction),
        "damage_penalty":      float(rr.damage_penalty),
        "qc": {
            "expected_weight":      float(rr.expected_weight)       if rr.expected_weight      is not None else None,
            "received_weight":      float(rr.received_weight)       if rr.received_weight      is not None else None,
            "stone_count_expected": rr.stone_count_expected,
            "stone_count_received": rr.stone_count_received,
            "hallmark_ok":          rr.hallmark_ok,
            "packaging_ok":         rr.packaging_ok,
            "damage_notes":         rr.damage_notes,
            "qc_result":            rr.qc_result,
            "qc_notes":             rr.qc_notes,
        },
        "timeline": [
            {
                "from_status": lg.from_status,
                "to_status":   lg.to_status,
                "note":        lg.note,
                "changed_by":  lg.changed_by.get_full_name() or lg.changed_by.username if lg.changed_by else "System",
                "changed_at":  lg.changed_at.strftime("%b %d, %Y %H:%M"),
            }
            for lg in rr.stage_logs.all()
        ],
    })
    return base


@staff_member_required
@require_http_methods(["GET"])
def returns_list_api(request):
    """List return requests with optional filters."""
    qs = ReturnRequest.objects.select_related("customer", "order").order_by("-created_at")
    status_f   = request.GET.get("status")
    priority_f = request.GET.get("priority")
    search_f   = request.GET.get("q", "").strip()
    if status_f:
        qs = qs.filter(status=status_f)
    if priority_f:
        qs = qs.filter(priority=priority_f)
    if search_f:
        qs = qs.filter(
            Q(product_name__icontains=search_f) |
            Q(customer__username__icontains=search_f) |
            Q(customer__email__icontains=search_f) |
            Q(order__id__icontains=search_f)
        )
    returns = [_serialize_return(r) for r in qs[:200]]
    return JsonResponse({"success": True, "returns": returns, "total": len(returns)})


@staff_member_required
@require_http_methods(["GET"])
def returns_analytics_api(request):
    """KPIs, alerts, stage counts, and chart data for the analytics panels."""
    from django.utils import timezone as tz
    from datetime import timedelta, date

    now = tz.now()
    this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # ── KPIs ────────────────────────────────────────────────
    total         = ReturnRequest.objects.count()
    pending_review = ReturnRequest.objects.filter(status="review").count()
    pending_refund = ReturnRequest.objects.filter(status="refund_pending").count()
    refunded_month = ReturnRequest.objects.filter(
        status="refund_completed", refunded_at__gte=this_month_start
    ).aggregate(t=Sum("final_refund_amount"))["t"] or 0
    delivered_total = Order.objects.filter(status="delivered").count()
    return_rate = round((total / delivered_total * 100), 1) if delivered_total else 0

    # Avg resolution (days from requested → refund_completed)
    resolved = ReturnRequest.objects.filter(status="refund_completed", refunded_at__isnull=False)
    avg_res = 0
    if resolved.exists():
        deltas = [(r.refunded_at - r.created_at).days for r in resolved]
        avg_res = round(sum(deltas) / len(deltas), 1)

    # ── Smart Alerts ────────────────────────────────────────
    alerts = []
    hv = ReturnRequest.objects.filter(order_amount__gte=10000, status__in=["requested", "review"]).count()
    if hv:
        alerts.append({"type": "high_value",  "msg": f"{hv} High-Value Return{'s' if hv>1 else ''} Awaiting Review",  "count": hv, "severity": "warning"})

    stale_threshold = now - timedelta(days=7)
    stale = ReturnRequest.objects.filter(
        created_at__lt=stale_threshold,
        status__in=["requested", "review", "approved", "pickup_scheduled"]
    ).count()
    if stale:
        alerts.append({"type": "stale", "msg": f"{stale} Return{'s' if stale>1 else ''} Pending > 7 Days", "count": stale, "severity": "danger"})

    qc_fail = ReturnRequest.objects.filter(qc_result="fail").count()
    if qc_fail:
        alerts.append({"type": "qc_fail", "msg": f"{qc_fail} QC Failure{'s' if qc_fail>1 else ''}", "count": qc_fail, "severity": "danger"})

    refund_q = ReturnRequest.objects.filter(status="refund_pending").aggregate(t=Sum("final_refund_amount"))["t"] or 0
    if refund_q > 0:
        alerts.append({"type": "refund_queue", "msg": f"Refund Queue ₹{refund_q:,.0f}", "count": 0, "severity": "warning"})

    # ── Stage counts & values ────────────────────────────────
    STAGES = ["requested", "review", "approved", "pickup_scheduled", "received", "quality_check", "refund_pending", "refund_completed", "rejected"]
    stage_counts = {}
    for s in STAGES:
        agg = ReturnRequest.objects.filter(status=s).aggregate(cnt=Count("id"), val=Sum("order_amount"))
        stage_counts[s] = {"count": agg["cnt"] or 0, "value": float(agg["val"] or 0)}

    # ── Return reasons breakdown ─────────────────────────────
    reason_data = list(
        ReturnRequest.objects.values("return_reason")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    # ── Refund trend last 30 days ─────────────────────────────
    trend = []
    for i in range(29, -1, -1):
        d = (now - timedelta(days=i)).date()
        amt = ReturnRequest.objects.filter(
            refunded_at__date=d, status="refund_completed"
        ).aggregate(t=Sum("final_refund_amount"))["t"] or 0
        trend.append({"date": str(d), "amount": float(amt)})

    # ── Top returned products ────────────────────────────────
    top_products = list(
        ReturnRequest.objects.values("product_name")
        .annotate(count=Count("id"), total_val=Sum("order_amount"))
        .order_by("-count")[:8]
    )

    # ── Recovery stats ───────────────────────────────────────
    recovery = {
        "resellable":    ReturnRequest.objects.filter(resale_status="resellable").count(),
        "repair_needed": ReturnRequest.objects.filter(resale_status="repair_needed").count(),
        "damaged":       ReturnRequest.objects.filter(resale_status="damaged").count(),
    }

    # ── Customer risk ────────────────────────────────────────
    cust_risk = list(
        ReturnRequest.objects.values("customer__id", "customer__username", "customer__email")
        .annotate(return_count=Count("id"), total_val=Sum("order_amount"))
        .order_by("-return_count")[:8]
    )

    return JsonResponse({
        "success": True,
        "kpis": {
            "total":           total,
            "pending_review":  pending_review,
            "pending_refund":  pending_refund,
            "refunded_month":  float(refunded_month),
            "return_rate":     return_rate,
            "avg_resolution":  avg_res,
        },
        "alerts":        alerts,
        "stage_counts":  stage_counts,
        "reason_data":   reason_data,
        "refund_trend":  trend,
        "top_products":  top_products,
        "recovery":      recovery,
        "customer_risk": cust_risk,
    })


@staff_member_required
@require_http_methods(["GET"])
def return_detail_api(request, return_id):
    rr = get_object_or_404(
        ReturnRequest.objects.select_related('order', 'customer'),
        id=return_id,
    )
    return JsonResponse({"success": True, "return": _serialize_return_detail(rr)})


@staff_member_required
@require_http_methods(["POST"])
def return_update_status_api(request, return_id):
    rr = get_object_or_404(ReturnRequest, id=return_id)
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    new_status = data.get("status")
    valid_statuses = [s[0] for s in ReturnRequest.STATUS_CHOICES]
    if new_status not in valid_statuses:
        return JsonResponse({"success": False, "error": "Invalid status."}, status=400)

    from django.utils import timezone as tz
    prev = rr.status
    rr.status = new_status
    # Stamp relevant timestamps
    if new_status == "approved"  and not rr.approved_at:  rr.approved_at = tz.now()
    if new_status == "received"  and not rr.received_at:  rr.received_at = tz.now()
    if new_status == "refund_completed":
        rr.refunded_at = tz.now()
        if rr.final_refund_amount is None:
            rr.final_refund_amount = rr.calculated_refund
    note = (data.get("note") or "").strip()
    rr.save()

    ReturnStageLog.objects.create(
        return_request=rr,
        from_status=prev,
        to_status=new_status,
        note=note,
        changed_by=request.user,
    )
    return JsonResponse({"success": True, "message": f"Status updated to '{new_status}'.", "return": _serialize_return(rr)})


@staff_member_required
@require_http_methods(["POST"])
def return_save_qc_api(request, return_id):
    rr = get_object_or_404(ReturnRequest, id=return_id)
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    def _f(val):
        try: return float(val) if val not in (None, "") else None
        except: return None
    def _i(val):
        try: return int(val) if val not in (None, "") else None
        except: return None

    rr.expected_weight      = _f(data.get("expected_weight"))
    rr.received_weight      = _f(data.get("received_weight"))
    rr.stone_count_expected = _i(data.get("stone_count_expected"))
    rr.stone_count_received = _i(data.get("stone_count_received"))
    rr.hallmark_ok          = data.get("hallmark_ok")   # bool or None
    rr.packaging_ok         = data.get("packaging_ok")  # bool or None
    rr.damage_notes         = (data.get("damage_notes")  or "").strip()
    qc_res                  = (data.get("qc_result")     or "").strip()
    if qc_res in ["pass", "fail", "investigate"]:
        rr.qc_result = qc_res
    rr.qc_notes = (data.get("qc_notes") or "").strip()
    # Map QC result → resale status
    qc_to_resale = {"pass": "resellable", "fail": "damaged", "investigate": "repair_needed"}
    if qc_res in qc_to_resale:
        rr.resale_status = qc_to_resale[qc_res]
    rr.save()

    return JsonResponse({"success": True, "message": "QC data saved.", "return": _serialize_return(rr)})


@staff_member_required
@require_http_methods(["POST"])
def return_process_refund_api(request, return_id):
    rr = get_object_or_404(ReturnRequest, id=return_id)
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    action = data.get("action")  # "approve" | "partial" | "reject"
    if action not in ("approve", "partial", "reject"):
        return JsonResponse({"success": False, "error": "Invalid action."}, status=400)

    from django.utils import timezone as tz
    prev = rr.status

    if action == "reject":
        rr.status        = "rejected"
        rr.admin_notes   = (rr.admin_notes + "\n" if rr.admin_notes else "") + f"[Rejected] {data.get('note','')}"
        note_text        = f"Refund rejected. {data.get('note','')}"
        rr.save()
    else:
        try:
            ship_ded   = float(data.get("shipping_deduction", 0))
            dmg_pen    = float(data.get("damage_penalty", 0))
            final_amt  = float(data.get("final_refund_amount") or rr.calculated_refund)
        except (ValueError, TypeError):
            return JsonResponse({"success": False, "error": "Invalid refund amounts."}, status=400)

        rr.shipping_deduction  = ship_ded
        rr.damage_penalty      = dmg_pen
        rr.final_refund_amount = final_amt
        rr.refund_reference    = (data.get("refund_reference") or "").strip()
        rr.status              = "refund_completed"
        rr.refunded_at         = tz.now()
        note_text              = f"{'Full' if action=='approve' else 'Partial'} refund ₹{final_amt:,.2f} approved."
        rr.save()

        # Notify customer
        UserNotification.objects.create(
            user=rr.customer,
            title=f"Refund Processed — {rr.rtn_id}",
            message=f"Your return {rr.rtn_id} has been processed. Refund of ₹{final_amt:,.2f} has been approved. Reference: {rr.refund_reference or 'N/A'}",
            notif_type="order_updated",
            related_order=rr.order,
        )

    ReturnStageLog.objects.create(
        return_request=rr,
        from_status=prev,
        to_status=rr.status,
        note=note_text,
        changed_by=request.user,
    )
    return JsonResponse({"success": True, "message": note_text, "return": _serialize_return(rr)})


@staff_member_required
@require_http_methods(["POST"])
def return_add_note_api(request, return_id):
    rr = get_object_or_404(ReturnRequest, id=return_id)
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)
    note = (data.get("note") or "").strip()
    if not note:
        return JsonResponse({"success": False, "error": "Note is empty."}, status=400)
    from django.utils import timezone as tz
    rr.admin_notes = (rr.admin_notes + "\n" if rr.admin_notes else "") + f"[{tz.now().strftime('%b %d %H:%M')}] {note}"
    rr.save(update_fields=["admin_notes", "updated_at"])
    ReturnStageLog.objects.create(
        return_request=rr, from_status=rr.status, to_status=rr.status,
        note=f"[Note] {note}", changed_by=request.user,
    )
    return JsonResponse({"success": True, "message": "Note added."})


# ════════════════════════════════════════════════════════════════════
#  MARKETING INTELLIGENCE — CAMPAIGN CRUD
# ════════════════════════════════════════════════════════════════════

def _serialize_campaign(c):
    return {
        "id":              c.id,
        "name":            c.name,
        "campaign_type":   c.campaign_type,
        "campaign_type_display": c.get_campaign_type_display(),
        "audience":        c.audience,
        "audience_display": c.get_audience_display(),
        "email_subject":   c.email_subject,
        "email_body_html": c.email_body_html,
        "whatsapp_message":c.whatsapp_message,
        "scheduled_at":    c.scheduled_at.isoformat() if c.scheduled_at else None,
        "status":          c.status,
        "sent_count":      c.sent_count,
        "opened_count":    c.opened_count,
        "clicked_count":   c.clicked_count,
        "created_at":      c.created_at.strftime("%b %d, %Y"),
    }


@staff_member_required
@require_http_methods(["GET"])
def campaigns_list_api(request):
    campaigns = Campaign.objects.all()
    return JsonResponse({"success": True, "campaigns": [_serialize_campaign(c) for c in campaigns]})


@staff_member_required
@require_http_methods(["POST"])
def campaign_create_api(request):
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    name = (data.get("name") or "").strip()
    if not name:
        return JsonResponse({"success": False, "error": "Campaign name is required."}, status=400)

    from django.utils.dateparse import parse_datetime
    sched = None
    if data.get("scheduled_at"):
        sched = parse_datetime(data["scheduled_at"])

    c = Campaign.objects.create(
        name            = name,
        campaign_type   = data.get("campaign_type", "email"),
        audience        = data.get("audience", "all"),
        email_subject   = data.get("email_subject", ""),
        email_body_html = data.get("email_body_html", ""),
        whatsapp_message= data.get("whatsapp_message", ""),
        scheduled_at    = sched,
        status          = "scheduled" if sched else "draft",
    )
    return JsonResponse({"success": True, "campaign": _serialize_campaign(c)})


@staff_member_required
@require_http_methods(["POST"])
def campaign_update_api(request, campaign_id):
    c = get_object_or_404(Campaign, id=campaign_id)
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    from django.utils.dateparse import parse_datetime
    sched = None
    if data.get("scheduled_at"):
        sched = parse_datetime(data["scheduled_at"])

    c.name             = (data.get("name") or c.name).strip()
    c.campaign_type    = data.get("campaign_type", c.campaign_type)
    c.audience         = data.get("audience", c.audience)
    c.email_subject    = data.get("email_subject", c.email_subject)
    c.email_body_html  = data.get("email_body_html", c.email_body_html)
    c.whatsapp_message = data.get("whatsapp_message", c.whatsapp_message)
    c.scheduled_at     = sched
    if c.status == "draft" and sched:
        c.status = "scheduled"
    c.save()
    return JsonResponse({"success": True, "campaign": _serialize_campaign(c)})


@staff_member_required
@require_http_methods(["POST"])
def campaign_delete_api(request, campaign_id):
    c = get_object_or_404(Campaign, id=campaign_id)
    c.delete()
    return JsonResponse({"success": True})


@staff_member_required
@require_http_methods(["POST"])
def campaign_send_api(request, campaign_id):
    """Send campaign immediately to the target audience."""
    c = get_object_or_404(Campaign, id=campaign_id)
    if c.status == "sent":
        return JsonResponse({"success": False, "error": "Campaign already sent."}, status=400)

    sent_email = 0
    sent_wa    = 0
    errors     = []

    # Resolve audience → queryset of users with email/phone
    from django.contrib.auth import get_user_model
    U = get_user_model()
    qs = U.objects.filter(is_active=True)

    if c.audience == "vip":
        vip_ids = Order.objects.filter(status="delivered").values("user_id").annotate(
            t=Sum("total")).filter(t__gte=15000).values_list("user_id", flat=True)
        qs = qs.filter(id__in=vip_ids)
    elif c.audience == "repeat":
        repeat_ids = Order.objects.values("user_id").annotate(cnt=Count("id")).filter(
            cnt__gte=2).values_list("user_id", flat=True)
        qs = qs.filter(id__in=repeat_ids)
    elif c.audience == "high_value":
        hv_ids = Order.objects.filter(total__gte=10000).values_list("user_id", flat=True).distinct()
        qs = qs.filter(id__in=hv_ids)
    elif c.audience == "inactive":
        cutoff = timezone.now() - timedelta(days=60)
        active_ids = Order.objects.filter(created_at__gte=cutoff).values_list("user_id", flat=True).distinct()
        qs = qs.exclude(id__in=active_ids)
    elif c.audience == "new":
        new_ids = Order.objects.values("user_id").annotate(cnt=Count("id")).filter(
            cnt=1).values_list("user_id", flat=True)
        qs = qs.filter(id__in=new_ids)

    # Email sending
    if c.campaign_type in ["email", "both"] and c.email_subject and c.email_body_html:
        try:
            from django.core.mail import EmailMessage
            from django.core.mail.backends.smtp import EmailBackend
            email_host     = APISetting.get_setting("EMAIL_HOST", "smtp.gmail.com")
            email_port     = int(APISetting.get_setting("EMAIL_PORT", "587") or 587)
            email_user     = APISetting.get_setting("EMAIL_HOST_USER", "")
            email_pass     = APISetting.get_setting("EMAIL_HOST_PASSWORD", "")
            email_from     = APISetting.get_setting("DEFAULT_FROM_EMAIL", email_user)
            if email_user and email_pass:
                conn = EmailBackend(
                    host=email_host, port=email_port,
                    username=email_user, password=email_pass,
                    use_tls=True, fail_silently=True,
                )
                for user in qs.exclude(email=""):
                    try:
                        msg = EmailMessage(
                            subject=c.email_subject,
                            body=c.email_body_html,
                            from_email=email_from,
                            to=[user.email],
                            connection=conn,
                        )
                        msg.content_subtype = "html"
                        msg.send()
                        sent_email += 1
                    except Exception as e:
                        errors.append(f"Email to {user.email}: {str(e)[:60]}")
        except Exception as e:
            errors.append(f"Email backend setup failed: {str(e)[:80]}")

    # WhatsApp sending via Twilio
    if c.campaign_type in ["whatsapp", "both"] and c.whatsapp_message:
        try:
            account_sid = APISetting.get_setting("TWILIO_ACCOUNT_SID", "")
            auth_token  = APISetting.get_setting("TWILIO_AUTH_TOKEN", "")
            from_number = APISetting.get_setting("TWILIO_WHATSAPP_FROM", "+14155238886")
            if account_sid and auth_token:
                from twilio.rest import Client as TwilioClient
                twilio = TwilioClient(account_sid, auth_token)
                for user in qs:
                    phone = getattr(user, "phone_number", None) or getattr(
                        user, "customerprofile", None) and user.customerprofile.phone
                    if not phone:
                        continue
                    try:
                        twilio.messages.create(
                            body=c.whatsapp_message,
                            from_=f"whatsapp:{from_number}",
                            to=f"whatsapp:{phone}",
                        )
                        sent_wa += 1
                    except Exception as e:
                        errors.append(f"WA to {phone}: {str(e)[:60]}")
        except ImportError:
            errors.append("Twilio not installed. Run: pip install twilio")
        except Exception as e:
            errors.append(f"WhatsApp error: {str(e)[:80]}")

    c.status     = "sent"
    c.sent_count = sent_email + sent_wa
    c.save()

    return JsonResponse({
        "success":     True,
        "sent_email":  sent_email,
        "sent_wa":     sent_wa,
        "errors":      errors[:5],   # show first 5 errors only
        "total_sent":  sent_email + sent_wa,
    })


# ── AI Content Generation ────────────────────────────────

@staff_member_required
@require_http_methods(["POST"])
def campaign_generate_ai_api(request):
    """Generate email subject/body + WhatsApp message using OpenAI."""
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    product  = (data.get("product") or "Jewellery Collection").strip()
    audience = (data.get("audience") or "All Customers").strip()
    tone     = (data.get("tone") or "premium").strip()

    api_key = APISetting.get_setting("OPENAI_API_KEY", "")
    if not api_key:
        # Return smart template-based fallback if no OpenAI key
        return JsonResponse({
            "success": True,
            "ai_used": False,
            "subject": f"✨ Exclusive Offer on {product} — Limited Time!",
            "email_body": (
                f"<p>Dear Valued Customer,</p>"
                f"<p>We are delighted to present our exquisite <strong>{product}</strong> — "
                f"crafted with precision and designed to make every moment special.</p>"
                f"<p>As one of our valued {audience}, we are offering you an exclusive priority access. "
                f"Don't miss this chance to own a piece of timeless elegance.</p>"
                f"<p><a href='#' style='background:#c4a35a;color:#fff;padding:10px 24px;border-radius:6px;text-decoration:none;'>Shop Now</a></p>"
                f"<p>Warm regards,<br/>Princess Jewellery Team</p>"
            ),
            "whatsapp": f"✨ Exclusive offer on {product} — just for you! Shop now before it's gone. Reply STOP to unsubscribe.",
        })

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        model = APISetting.get_setting("OPENAI_MODEL", "gpt-3.5-turbo")

        prompt = (
            f"You are a marketing expert for a luxury Indian jewellery brand called Princess Jewellery.\n"
            f"Create a marketing campaign for:\n"
            f"  Product: {product}\n"
            f"  Audience: {audience}\n"
            f"  Tone: {tone}\n\n"
            f"Respond ONLY in this exact JSON format (no extra text):\n"
            f'{{"subject":"...","email_body":"<p>...</p>","whatsapp":"..."}}'
        )
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.75,
            max_tokens=600,
        )
        raw = resp.choices[0].message.content.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw)
        return JsonResponse({
            "success":    True,
            "ai_used":    True,
            "subject":    result.get("subject", ""),
            "email_body": result.get("email_body", ""),
            "whatsapp":   result.get("whatsapp", ""),
        })
    except Exception:
        pass  # Fall through to template fallback below

    # Template-based fallback (OpenAI unavailable or quota exceeded)
    tone_greet = {"luxury": "We are delighted to present", "casual": "Hey! Check out", "urgent": "⚡ Last chance for"}.get(tone, "We are pleased to present")
    return JsonResponse({
        "success": True,
        "ai_used": False,
        "subject": f"✨ Exclusive Offer on {product} — Limited Time!",
        "email_body": (
            f"<p>Dear Valued Customer,</p>"
            f"<p>{tone_greet} our exquisite <strong>{product}</strong> — "
            f"crafted with precision and designed to make every moment special.</p>"
            f"<p>As one of our valued {audience} customers, we are offering you exclusive priority access. "
            f"Don't miss this chance to own a piece of timeless elegance.</p>"
            f"<p><a href='#' style='background:#c4a35a;color:#fff;padding:10px 24px;border-radius:6px;text-decoration:none;'>Shop Now</a></p>"
            f"<p>Warm regards,<br/>Princess Jewellery Team</p>"
        ),
        "whatsapp": f"✨ Exclusive offer on {product} — just for you! Shop now before it's gone. Reply STOP to unsubscribe.",
    })


# ── Marketing Analytics ──────────────────────────────────

@staff_member_required
@require_http_methods(["GET"])
def marketing_analytics_api(request):
    """Campaign stats + audience size breakdown."""
    campaigns = Campaign.objects.all()

    # Campaign performance table
    rows = [_serialize_campaign(c) for c in campaigns]

    # Audience size stats
    from django.contrib.auth import get_user_model
    U = get_user_model()
    total_users = U.objects.filter(is_active=True).count()

    vip_ids = Order.objects.filter(status="delivered").values("user_id").annotate(
        t=Sum("total")).filter(t__gte=15000).values_list("user_id", flat=True)
    repeat_ids = Order.objects.values("user_id").annotate(cnt=Count("id")).filter(
        cnt__gte=2).values_list("user_id", flat=True)

    cutoff = timezone.now() - timedelta(days=60)
    active_ids = Order.objects.filter(created_at__gte=cutoff).values_list("user_id", flat=True).distinct()

    audience_sizes = {
        "all":        total_users,
        "vip":        len(set(vip_ids)),
        "repeat":     len(set(repeat_ids)),
        "high_value": Order.objects.filter(total__gte=10000).values("user_id").distinct().count(),
        "inactive":   U.objects.filter(is_active=True).exclude(id__in=active_ids).count(),
        "new":        Order.objects.values("user_id").annotate(cnt=Count("id")).filter(cnt=1).count(),
    }

    total_sent    = Campaign.objects.filter(status="sent").aggregate(t=Sum("sent_count"))["t"] or 0
    total_opened  = Campaign.objects.filter(status="sent").aggregate(t=Sum("opened_count"))["t"] or 0
    total_clicked = Campaign.objects.filter(status="sent").aggregate(t=Sum("clicked_count"))["t"] or 0
    sent_30d      = Campaign.objects.filter(status="sent", updated_at__gte=timezone.now()-timedelta(days=30)).count()

    return JsonResponse({
        "success":       True,
        "campaigns":     rows,
        "audience_sizes":audience_sizes,
        "kpis": {
            "total_campaigns":  campaigns.count(),
            "sent_campaigns":   campaigns.filter(status="sent").count(),
            "draft_campaigns":  campaigns.filter(status="draft").count(),
            "total_sent":       total_sent,
            "total_opened":     total_opened,
            "total_clicked":    total_clicked,
            "sent_30d":         sent_30d,
            "open_rate":        round(total_opened / total_sent * 100, 1) if total_sent else 0,
        },
    })


# ── Automation Config ────────────────────────────────────

@staff_member_required
@require_http_methods(["GET"])
def automation_config_api(request):
    cfg, _ = AutomationConfig.objects.get_or_create(id=1)
    return JsonResponse({"success": True, "config": {
        "abandoned_cart_enabled":     cfg.abandoned_cart_enabled,
        "abandoned_cart_delay_hours": cfg.abandoned_cart_delay_hours,
        "abandoned_cart_msg":         cfg.abandoned_cart_msg,
        "first_purchase_enabled":     cfg.first_purchase_enabled,
        "first_purchase_msg":         cfg.first_purchase_msg,
        "birthday_enabled":           cfg.birthday_enabled,
        "birthday_discount":          cfg.birthday_discount,
        "vip_enabled":                cfg.vip_enabled,
        "vip_threshold":              float(cfg.vip_threshold),
        "winback_enabled":            cfg.winback_enabled,
        "winback_days":               cfg.winback_days,
        "winback_msg":                cfg.winback_msg,
    }})


@staff_member_required
@require_http_methods(["POST"])
def automation_config_save_api(request):
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    cfg, _ = AutomationConfig.objects.get_or_create(id=1)
    fields = [
        "abandoned_cart_enabled", "abandoned_cart_delay_hours", "abandoned_cart_msg",
        "first_purchase_enabled", "first_purchase_msg",
        "birthday_enabled", "birthday_discount",
        "vip_enabled", "vip_threshold",
        "winback_enabled", "winback_days", "winback_msg",
    ]
    for f in fields:
        if f in data:
            setattr(cfg, f, data[f])
    cfg.save()
    return JsonResponse({"success": True})


# ════════════════════════════════════════════════════════════════════
#  FINANCE INTELLIGENCE — OVERVIEW & INVENTORY
# ════════════════════════════════════════════════════════════════════

@staff_member_required
@require_http_methods(["GET"])
def finance_overview_api(request):
    """Executive finance overview KPIs."""
    today = timezone.now().date()
    month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    year_start  = timezone.now().replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

    today_rev  = Order.objects.filter(created_at__date=today, status__in=["delivered","processing","packed","shipped","out_for_delivery"]).aggregate(t=Sum("total"))["t"] or 0
    month_rev  = Order.objects.filter(created_at__gte=month_start, status__in=["delivered","processing","packed","shipped","out_for_delivery"]).aggregate(t=Sum("total"))["t"] or 0
    year_rev   = Order.objects.filter(created_at__gte=year_start,  status__in=["delivered","processing","packed","shipped","out_for_delivery"]).aggregate(t=Sum("total"))["t"] or 0
    total_rev  = Order.objects.filter(status__in=["delivered","processing","packed","shipped","out_for_delivery"]).aggregate(t=Sum("total"))["t"] or 0

    pending_refunds = ReturnRequest.objects.filter(status="refund_pending").aggregate(t=Sum("final_refund_amount"))["t"] or 0
    refunded_month  = ReturnRequest.objects.filter(status="refund_completed", refunded_at__gte=month_start).aggregate(t=Sum("final_refund_amount"))["t"] or 0
    total_orders    = Order.objects.count()
    delivered_cnt   = Order.objects.filter(status="delivered").count()
    cancelled_cnt   = Order.objects.filter(status="cancelled").count()
    from django.db.models import Avg, Max
    avg_order_val   = Order.objects.filter(status="delivered").aggregate(a=Avg("total"))["a"] or 0

    # Monthly revenue last 6 months for chart
    monthly = []
    try:
        from dateutil.relativedelta import relativedelta as _rd
        _has_rd = True
    except ImportError:
        _has_rd = False
    for i in range(5, -1, -1):
        if _has_rd:
            m_start = (timezone.now() - _rd(months=i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            m_end   = m_start + _rd(months=1)
        else:
            # Fallback: just use current month
            m_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            m_end   = timezone.now()
        rev = Order.objects.filter(
            created_at__gte=m_start, created_at__lt=m_end,
            status__in=["delivered","processing","packed","shipped","out_for_delivery"]
        ).aggregate(t=Sum("total"))["t"] or 0
        monthly.append({"label": m_start.strftime("%b %Y"), "revenue": float(rev)})

    return JsonResponse({
        "success": True,
        "kpis": {
            "today_revenue":    float(today_rev),
            "month_revenue":    float(month_rev),
            "year_revenue":     float(year_rev),
            "total_revenue":    float(total_rev),
            "pending_refunds":  float(pending_refunds),
            "refunded_month":   float(refunded_month),
            "total_orders":     total_orders,
            "delivered_orders": delivered_cnt,
            "cancelled_orders": cancelled_cnt,
            "avg_order_value":  float(avg_order_val),
        },
        "monthly_revenue": monthly,
    })


@staff_member_required
@require_http_methods(["GET"])
def finance_inventory_api(request):
    """Jewellery inventory value analysis (product-category based)."""
    # High-value orders
    hv_orders = list(
        Order.objects.filter(total__gte=10000, status__in=["delivered","processing","packed","shipped"])
        .select_related("user")
        .order_by("-total")[:10]
        .values("id", "total", "status", "created_at", "user__first_name", "user__last_name", "user__email")
    )
    for o in hv_orders:
        o["total_amount"]  = float(o.pop("total", 0))
        o["created_at"]    = o["created_at"].strftime("%b %d, %Y") if o["created_at"] else ""
        o["customer_name"] = f"{o.pop('user__first_name','')} {o.pop('user__last_name','')}".strip() or o.pop("user__email","")
        o.pop("user__email", None)

    # Category revenue breakdown
    cat_breakdown = list(
        OrderItem.objects.select_related("product__category")
        .values("product__category__name")
        .annotate(
            total_qty = Count("id"),
            total_val = Sum(F("price") * F("quantity"))
        )
        .order_by("-total_val")[:8]
    )
    for row in cat_breakdown:
        row["total_val"] = float(row["total_val"] or 0)

    # Slow-moving products (ordered before, not since 90 days)
    cutoff_90 = timezone.now() - timedelta(days=90)
    from django.db.models import Max as DMax
    slow_prods = list(
        Product.objects.filter(is_active=True)
        .annotate(last_order=DMax("orderitem__order__created_at"))
        .filter(Q(last_order__lt=cutoff_90) | Q(last_order=None))
        .values("name", "last_order", "price")
        .order_by("last_order")[:8]
    )
    for p in slow_prods:
        p["price"]      = float(p["price"] or 0)
        p["last_order"] = p["last_order"].strftime("%b %d, %Y") if p["last_order"] else "Never sold"

    # Total inventory value (all active products × their price)
    inv_value = Product.objects.filter(is_active=True).aggregate(
        t=Sum("price"), cnt=Count("id")
    )

    return JsonResponse({
        "success":           True,
        "inventory_value":   float(inv_value["t"] or 0),
        "active_products":   inv_value["cnt"] or 0,
        "high_value_orders": hv_orders,
        "category_breakdown":cat_breakdown,
        "slow_movers":       slow_prods,
    })


@staff_member_required
@require_http_methods(["GET"])
def finance_copilot_api(request):
    """AI-generated business insights based on real data."""
    # Compute real metrics to base insights on
    month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    prev_start  = (month_start - timedelta(days=1)).replace(day=1)

    cur_rev  = float(Order.objects.filter(created_at__gte=month_start, status="delivered").aggregate(t=Sum("total"))["t"] or 0)
    prev_rev = float(Order.objects.filter(created_at__gte=prev_start, created_at__lt=month_start, status="delivered").aggregate(t=Sum("total"))["t"] or 0)
    rev_chg  = round((cur_rev - prev_rev) / prev_rev * 100, 1) if prev_rev else 0

    return_rate = 0
    total_del = Order.objects.filter(status="delivered").count()
    total_ret = ReturnRequest.objects.count()
    if total_del:
        return_rate = round(total_ret / total_del * 100, 1)

    top_cat = (
        OrderItem.objects.values("product__category__name")
        .annotate(v=Sum(F("price") * F("quantity")))
        .order_by("-v").first()
    )
    top_cat_name = top_cat["product__category__name"] if top_cat else "N/A"

    low_stock = Product.objects.filter(is_active=True, stock__lte=5).count()

    api_key = APISetting.get_setting("OPENAI_API_KEY", "")
    insights = []

    if api_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            prompt = (
                f"You are a business analyst for Princess Jewellery (Indian luxury jewellery brand).\n"
                f"Current month revenue: ₹{cur_rev:,.0f} ({rev_chg:+.1f}% vs last month)\n"
                f"Return rate: {return_rate}%\n"
                f"Top category: {top_cat_name}\n"
                f"Low stock products: {low_stock}\n\n"
                f"Generate 4 actionable business insights as JSON array:\n"
                f'[{{"icon":"📈","title":"...","detail":"...","action":"..."}}]'
            )
            resp = client.chat.completions.create(
                model=APISetting.get_setting("OPENAI_MODEL", "gpt-3.5-turbo"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500,
            )
            raw = resp.choices[0].message.content.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            insights = json.loads(raw)
        except Exception:
            pass

    # Fallback rule-based insights
    if not insights:
        insights = []
        if rev_chg > 0:
            insights.append({"icon": "📈", "title": f"Revenue Up {rev_chg}% This Month", "detail": f"Current month: ₹{cur_rev:,.0f} vs ₹{prev_rev:,.0f} last month.", "action": "Analyse top SKUs driving growth"})
        elif rev_chg < 0:
            insights.append({"icon": "📉", "title": f"Revenue Down {abs(rev_chg)}% This Month", "detail": f"From ₹{prev_rev:,.0f} to ₹{cur_rev:,.0f}.", "action": "Review pricing & run a campaign"})
        if return_rate > 10:
            insights.append({"icon": "↩️", "title": f"High Return Rate: {return_rate}%", "detail": "Above 10% return rate — common causes: size issues, quality concerns.", "action": "Improve size guide & QC process"})
        if low_stock > 0:
            insights.append({"icon": "⚠️", "title": f"{low_stock} Products Low on Stock", "detail": "These products may miss sales opportunities.", "action": "Restock before running campaigns"})
        if top_cat_name != "N/A":
            insights.append({"icon": "💎", "title": f"Top Category: {top_cat_name}", "detail": "This category is your strongest revenue driver this month.", "action": f"Increase {top_cat_name} inventory & ad spend"})
        insights.append({"icon": "🎯", "title": "Launch a VIP Campaign", "detail": "VIP customers typically generate 40-60% of revenue.", "action": "Use Campaign Builder → Audience: VIP"})

    health_score = min(100, max(0, 60 + min(rev_chg, 20) - max(return_rate - 5, 0) * 2))

    return JsonResponse({
        "success":       True,
        "insights":      insights[:5],
        "health_score":  round(health_score),
        "metrics": {
            "cur_revenue":    cur_rev,
            "prev_revenue":   prev_rev,
            "rev_change_pct": rev_chg,
            "return_rate":    return_rate,
            "top_category":   top_cat_name,
            "low_stock_count":low_stock,
        },
    })


# ════════════════════════════════════════════════════════════════════
#  API SETTINGS MANAGEMENT
# ════════════════════════════════════════════════════════════════════

@staff_member_required
@require_http_methods(["GET"])
def api_settings_list_api(request):
    items = APISetting.objects.all()
    return JsonResponse({"success": True, "settings": [{
        "key":         s.key,
        "category":    s.category,
        "is_secret":   s.is_secret,
        "description": s.description,
        "has_value":   bool(s.value),
        "updated_at":  s.updated_at.strftime("%b %d, %Y %H:%M"),
        # Never send the actual secret value to frontend
        "display_value": "••••••••" if s.is_secret and s.value else (s.value[:30] if s.value else "—"),
    } for s in items]})


@staff_member_required
@require_http_methods(["POST"])
def api_setting_save_api(request):
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    key = (data.get("key") or "").strip().upper().replace(" ", "_")
    if not key:
        return JsonResponse({"success": False, "error": "Key is required."}, status=400)

    raw_value   = data.get("value", "")
    category    = data.get("category", "other")
    is_secret   = bool(data.get("is_secret", True))
    description = (data.get("description") or "").strip()

    obj, created = APISetting.objects.get_or_create(key=key)
    obj.category    = category
    obj.is_secret   = is_secret
    obj.description = description
    # Only update value if a new one was provided (empty = keep existing)
    if raw_value:
        obj.set_value(raw_value)
    obj.save()

    return JsonResponse({"success": True, "created": created})


@staff_member_required
@require_http_methods(["POST"])
def api_setting_delete_api(request, key):
    APISetting.objects.filter(key=key).delete()
    return JsonResponse({"success": True})
