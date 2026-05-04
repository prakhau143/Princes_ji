from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from store.models import Order, Product, Category, NewsletterSubscriber, ContactMessage
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.conf import settings
import json

@staff_member_required
def admin_dashboard(request):
    # Basic counts
    total_orders = Order.objects.count()
    total_sales = Order.objects.aggregate(total=Sum('total'))['total'] or 0
    total_products = Product.objects.count()
    total_customers = User.objects.filter(is_staff=False).count()
    
    # Recent orders (last 5)
    orders = Order.objects.select_related('user').order_by('-created_at')[:5]
    
    # All orders for orders section
    all_orders = Order.objects.select_related('user').order_by('-created_at')
    
    # Products with category info
    products = Product.objects.select_related('category').order_by('-created_at')
    
    # Categories for product form
    categories = Category.objects.filter(is_active=True)
    
    # Customers with order stats
    customers = User.objects.filter(is_staff=False).annotate(
        order_count=Count('order'),
        lifetime_value=Sum('order__total')
    ).order_by('-date_joined')
    
    # Analytics data
    thirty_days_ago = timezone.now() - timedelta(days=30)
    monthly_revenue = Order.objects.filter(
        created_at__gte=thirty_days_ago
    ).aggregate(total=Sum('total'))['total'] or 0
    
    # Top selling product (simplified)
    top_product = Product.objects.first()  # You can enhance this with actual sales data
    
    active_customers = User.objects.filter(
        is_staff=False,
        last_login__gte=thirty_days_ago
    ).count()
    
    # Subscribers and Messages data
    subscribers = NewsletterSubscriber.objects.filter(is_active=True).order_by('-subscribed_at')
    total_subscribers = subscribers.count()
    
    customer_messages = ContactMessage.objects.order_by('-created_at')
    total_messages = customer_messages.count()
    unread_messages = customer_messages.filter(is_read=False).count()
    
    # Order status choices
    order_status_choices = Order.STATUS_CHOICES
    
    return render(request, 'enhanced_admin_dashboard.html', {
        'total_orders': total_orders,
        'total_sales': total_sales,
        'total_products': total_products,
        'total_customers': total_customers,
        'total_subscribers': total_subscribers,
        'total_messages': total_messages,
        'unread_messages': unread_messages,
        'orders': orders,
        'all_orders': all_orders,
        'products': products,
        'categories': categories,
        'customers': customers,
        'subscribers': subscribers,
        'customer_messages': customer_messages,
        'monthly_revenue': monthly_revenue,
        'top_product': top_product,
        'active_customers': active_customers,
        'order_status_choices': order_status_choices,
        'conversion_rate': 2.5,  # You can calculate this based on your metrics
    })

@staff_member_required
def remove_subscriber(request, subscriber_id):
    if request.method == 'POST':
        try:
            subscriber = get_object_or_404(NewsletterSubscriber, id=subscriber_id)
            subscriber.delete()
            return JsonResponse({'success': True, 'message': 'Subscriber removed successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@staff_member_required
def get_message(request, message_id):
    try:
        message = get_object_or_404(ContactMessage, id=message_id)
        return JsonResponse({
            'success': True,
            'message': {
                'id': message.id,
                'name': message.name,
                'email': message.email,
                'subject': message.subject,
                'message': message.message,
                'created_at': message.created_at.strftime('%B %d, %Y at %I:%M %p'),
                'is_read': message.is_read,
                'is_replied': message.is_replied
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@staff_member_required
def mark_message_read(request, message_id):
    if request.method == 'POST':
        try:
            message = get_object_or_404(ContactMessage, id=message_id)
            message.is_read = True
            message.save()
            return JsonResponse({'success': True, 'message': 'Message marked as read'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@staff_member_required
def reply_message(request):
    if request.method == 'POST':
        try:
            message_id = request.POST.get('message_id')
            to_email = request.POST.get('to_email')
            to_name = request.POST.get('to_name')
            subject = request.POST.get('subject')
            reply_message = request.POST.get('reply_message')
            
            # Send reply email
            full_message = f"Dear {to_name},\n\n{reply_message}\n\nBest regards,\nPrincess Jewelry Team"
            
            send_mail(
                subject,
                full_message,
                settings.DEFAULT_FROM_EMAIL,
                [to_email],
                fail_silently=False,
            )
            
            # Mark original message as replied
            message = get_object_or_404(ContactMessage, id=message_id)
            message.is_read = True
            message.is_replied = True
            message.save()
            
            return JsonResponse({'success': True, 'message': 'Reply sent successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@staff_member_required
def send_newsletter(request):
    if request.method == 'POST':
        try:
            subject = request.POST.get('subject')
            message = request.POST.get('message')
            
            # Get all active subscribers
            subscribers = NewsletterSubscriber.objects.filter(is_active=True)
            subscriber_emails = [sub.email for sub in subscribers]
            
            if subscriber_emails:
                # Send newsletter to all subscribers
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    subscriber_emails,
                    fail_silently=False,
                )
                
                return JsonResponse({
                    'success': True, 
                    'message': f'Newsletter sent to {len(subscriber_emails)} subscribers'
                })
            else:
                return JsonResponse({'success': False, 'error': 'No active subscribers found'})
                
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})
