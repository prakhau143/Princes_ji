"""
URL configuration for ecommerce project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from store.views import home_view
from store.admin_dashboard import admin_dashboard, remove_subscriber, get_message, mark_message_read, reply_message, send_newsletter
from store.admin_dashboard_views import admin_update_order_status
from store.admin_api import search_api, export_orders, export_products, export_customers, filter_orders, add_product, get_notifications, mark_notification_read, mark_all_notifications_read, customer_detail_api, edit_product_api, delete_product_api, get_product_api
from store.auth_views import login_view, register_view, logout_view, forgot_password_view, verify_otp_view, reset_password_view, resend_otp

urlpatterns = [
    path('admin/', admin.site.urls),
    path('admin-dashboard/', admin_dashboard, name='admin-dashboard'),
    path('admin-dashboard/update-order-status/<int:order_id>/', admin_update_order_status, name='admin-update-order-status'),
    path('admin-dashboard/api/search/', search_api, name='admin-search-api'),
    path('admin-dashboard/api/filter-orders/', filter_orders, name='admin-filter-orders'),
    path('admin-dashboard/api/add-product/', add_product, name='add-product'),
    path('admin-dashboard/api/notifications/', get_notifications, name='get-notifications'),
    path('admin-dashboard/api/notifications/<int:notification_id>/read/', mark_notification_read, name='mark_notification_read'),
    path('admin-dashboard/api/notifications/mark-all-read/', mark_all_notifications_read, name='mark_all_notifications_read'),
    path('admin-dashboard/api/customer/<int:customer_id>/', customer_detail_api, name='customer_detail_api'),
    path('admin-dashboard/api/product/<int:product_id>/', get_product_api, name='get_product_api'),
    path('admin-dashboard/api/product/<int:product_id>/edit/', edit_product_api, name='edit_product_api'),
    path('admin-dashboard/api/product/<int:product_id>/delete/', delete_product_api, name='delete_product_api'),
    path('admin-dashboard/export/orders/', export_orders, name='export-orders'),
    path('admin-dashboard/export/products/', export_products, name='export-products'),
    path('admin-dashboard/export/customers/', export_customers, name='export-customers'),
    
    # Admin Dashboard - Subscriber and Message Management
    path('admin-dashboard/remove-subscriber/<int:subscriber_id>/', remove_subscriber, name='remove-subscriber'),
    path('admin-dashboard/get-message/<int:message_id>/', get_message, name='get-message'),
    path('admin-dashboard/mark-message-read/<int:message_id>/', mark_message_read, name='mark-message-read'),
    path('admin-dashboard/reply-message/', reply_message, name='reply-message'),
    path('admin-dashboard/send-newsletter/', send_newsletter, name='send-newsletter'),
    
    # Authentication URLs
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),
    path('forgot-password/', forgot_password_view, name='forgot_password'),
    path('verify-otp/', verify_otp_view, name='verify_otp'),
    path('reset-password/', reset_password_view, name='reset_password'),
    path('resend-otp/', resend_otp, name='resend_otp'),
    
    path('', home_view, name='home'),
    path('store/', include('store.urls')),
]

# Serve media and static files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)