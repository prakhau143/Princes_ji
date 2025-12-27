from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Order, Product, Notification

@receiver(post_save, sender=Order)
def create_order_notification(sender, instance, created, **kwargs):
    """Create notification when new order is placed"""
    if created:
        Notification.objects.create(
            title="New Order Placed",
            message=f"Order #{instance.id} placed by {instance.user.email} for ${instance.total}",
            notification_type="order_placed",
            related_order=instance
        )

@receiver(pre_save, sender=Order)
def order_status_notification(sender, instance, **kwargs):
    """Create notification when order is cancelled"""
    if instance.pk:  # Only for existing orders
        try:
            old_instance = Order.objects.get(pk=instance.pk)
            if old_instance.status != 'cancelled' and instance.status == 'cancelled':
                Notification.objects.create(
                    title="Order Cancelled",
                    message=f"Order #{instance.id} has been cancelled",
                    notification_type="order_cancelled",
                    related_order=instance
                )
        except Order.DoesNotExist:
            pass

@receiver(post_save, sender=Product)
def low_stock_notification(sender, instance, **kwargs):
    """Create notification for low stock products"""
    if instance.stock <= 5 and instance.stock > 0:
        # Check if notification already exists for this product
        existing = Notification.objects.filter(
            notification_type="low_stock",
            related_product=instance,
            is_read=False
        ).exists()
        
        if not existing:
            Notification.objects.create(
                title="Low Stock Alert",
                message=f"Product '{instance.name}' has low stock: {instance.stock} units remaining",
                notification_type="low_stock",
                related_product=instance
            )

@receiver(post_save, sender=User)
def new_customer_notification(sender, instance, created, **kwargs):
    """Create notification when new customer registers"""
    if created and not instance.is_staff:
        Notification.objects.create(
            title="New Customer Registered",
            message=f"New customer {instance.email} has registered",
            notification_type="new_customer"
        )
