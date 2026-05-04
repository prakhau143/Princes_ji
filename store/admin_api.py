from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404
from django.db.models import Q, Sum, Count, F, ExpressionWrapper, DecimalField
from django.db.models.functions import TruncDate, TruncMonth
import json
from .models import (
    Order,
    OrderItem,
    Product,
    Category,
    User,
    Notification,
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
)
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import csv
import io
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.conf import settings
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
            
            category = Category.objects.get(id=category_id, is_active=True)
            
            product = Product.objects.create(
                name=name,
                description=description,
                price=float(price),
                cost_price=float(cost_price or 0),
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
        categories = Category.objects.filter(is_active=True).order_by("name")
        return JsonResponse(
            {
                "success": True,
                "categories": [{"id": c.id, "name": c.name} for c in categories],
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
            "category": {"id": category.id, "name": category.name},
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
        order.save(update_fields=["status", "updated_at"])
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
    products = Product.objects.filter(is_active=True).order_by('name').values('id', 'name')
    return JsonResponse({"success": True, "products": list(products)})


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
