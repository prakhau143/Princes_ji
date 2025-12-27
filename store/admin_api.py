from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404
from django.db.models import Q, Sum
import json
from .models import Order, Product, Category, User, Notification
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import csv
from django.http import HttpResponse
from datetime import datetime
from django.utils import timezone
from datetime import timedelta

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
            order.phone or '-',
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
            category_id = request.POST.get('category')
            stock = request.POST.get('stock')
            image = request.FILES.get('image')
            
            if not all([name, price, category_id, stock]):
                return JsonResponse({'success': False, 'error': 'Missing required fields'})
            
            category = Category.objects.get(id=category_id)
            
            product = Product.objects.create(
                name=name,
                description=description,
                price=float(price),
                category=category,
                stock=int(stock),
                image=image
            )
            
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
            
            if not all([name, description, price, category_id, stock]):
                return JsonResponse({'success': False, 'error': 'All fields are required'})
            
            category = get_object_or_404(Category, id=category_id)
            
            # Update product fields
            product.name = name
            product.description = description
            product.price = float(price)
            product.category = category
            product.stock = int(stock)
            
            # Handle image upload if provided
            if 'image' in request.FILES:
                product.image = request.FILES['image']
            
            product.save()
            
            return JsonResponse({'success': True, 'message': 'Product updated successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

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
            'image_url': product.image.url if product.image else None
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
            Q(phone__icontains=search)
        )
    
    orders_data = []
    for order in orders.order_by('-created_at')[:50]:  # Limit to 50 results
        orders_data.append({
            'id': order.id,
            'customer': order.user.email,
            'phone': order.phone or '-',
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
