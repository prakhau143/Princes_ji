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
from store.admin_api import (
    search_api,
    export_orders,
    export_products,
    export_customers,
    filter_orders,
    add_product,
    get_notifications,
    mark_notification_read,
    mark_all_notifications_read,
    customer_detail_api,
    edit_product_api,
    toggle_product_active_api,
    delete_product_api,
    get_product_api,
    categories_api,
    delete_category_api,
    reels_api,
    toggle_reel_api,
    delete_reel_api,
    trust_badges_api,
    delete_trust_badge_api,
    marketing_spend_api,
    expense_ledger_api,
    profit_loss_api,
    reviews_admin_api,
    wishlist_analytics_api,
    homepage_section_content_api,
    homepage_section_products_api,
    delete_homepage_section_product_api,
    india_state_order_counts_api,
    toggle_homepage_section_product_api,
    update_homepage_section_product_api,
    low_stock_products_api,
    product_images_api,
    delete_product_image_api,
    set_primary_product_image_api,
    reorder_product_images_api,
    product_variants_api,
    delete_variant_api,
    order_lifecycle_logs_api,
    order_lifecycle_update_api,
    purchase_analytics_api,
    bulk_import_products_api,
    dashboard_graphs_api,
    dashboard_kpis_api,
    dashboard_top_products_api,
    dashboard_recent_orders_api,
    announcements_api,
    editorial_api,
    editorial_update_api,
    editorial_delete_api,
    editorial_toggle_api,
    product_list_simple_api,
    collections_api,
    collections_update_api,
    collections_delete_api,
    collections_toggle_api,
    collection_rows_api,
    collection_rows_update_api,
    collection_rows_delete_api,
    zoom_carousel_api,
    zoom_carousel_update_api,
    zoom_carousel_delete_api,
    zoom_carousel_toggle_api,
)
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
    path('admin-dashboard/api/product/<int:product_id>/toggle-active/', toggle_product_active_api, name='toggle_product_active_api'),
    path('admin-dashboard/api/product/<int:product_id>/delete/', delete_product_api, name='delete_product_api'),
    path('admin-dashboard/api/categories/', categories_api, name='categories_api'),
    path('admin-dashboard/api/categories/<int:category_id>/delete/', delete_category_api, name='delete_category_api'),
    path('admin-dashboard/api/reels/', reels_api, name='reels_api'),
    path('admin-dashboard/api/reels/<int:reel_id>/toggle/', toggle_reel_api, name='toggle_reel_api'),
    path('admin-dashboard/api/reels/<int:reel_id>/delete/', delete_reel_api, name='delete_reel_api'),
    path('admin-dashboard/api/trust-badges/', trust_badges_api, name='trust_badges_api'),
    path('admin-dashboard/api/trust-badges/<int:badge_id>/delete/', delete_trust_badge_api, name='delete_trust_badge_api'),
    path('admin-dashboard/api/marketing-spend/', marketing_spend_api, name='marketing_spend_api'),
    path('admin-dashboard/api/expense-ledger/', expense_ledger_api, name='expense_ledger_api'),
    path('admin-dashboard/api/profit-loss/', profit_loss_api, name='profit_loss_api'),
    path('admin-dashboard/api/reviews/', reviews_admin_api, name='reviews_admin_api'),
    path('admin-dashboard/api/wishlist-analytics/', wishlist_analytics_api, name='wishlist_analytics_api'),
    path('admin-dashboard/api/homepage-content/', homepage_section_content_api, name='homepage_section_content_api'),
    path('admin-dashboard/api/homepage-products/', homepage_section_products_api, name='homepage_section_products_api'),
    path('admin-dashboard/api/homepage-products/<int:item_id>/delete/', delete_homepage_section_product_api, name='delete_homepage_section_product_api'),
    path('admin-dashboard/api/homepage-products/<int:item_id>/toggle/', toggle_homepage_section_product_api, name='toggle_homepage_section_product_api'),
    path('admin-dashboard/api/homepage-products/<int:item_id>/update/', update_homepage_section_product_api, name='update_homepage_section_product_api'),
    path('admin-dashboard/api/india-state-orders/', india_state_order_counts_api, name='india_state_order_counts_api'),
    path('admin-dashboard/api/low-stock-products/', low_stock_products_api, name='low_stock_products_api'),
    path('admin-dashboard/api/products/<int:product_id>/images/', product_images_api, name='product_images_api'),
    path('admin-dashboard/api/product-images/<int:image_id>/delete/', delete_product_image_api, name='delete_product_image_api'),
    path('admin-dashboard/api/product-images/<int:image_id>/set-primary/', set_primary_product_image_api, name='set_primary_product_image_api'),
    path('admin-dashboard/api/products/<int:product_id>/images/reorder/', reorder_product_images_api, name='reorder_product_images_api'),
    path('admin-dashboard/api/products/<int:product_id>/variants/', product_variants_api, name='product_variants_api'),
    path('admin-dashboard/api/variants/<int:variant_id>/delete/', delete_variant_api, name='delete_variant_api'),
    path('admin-dashboard/api/orders/<int:order_id>/lifecycle/', order_lifecycle_logs_api, name='order_lifecycle_logs_api'),
    path('admin-dashboard/api/orders/<int:order_id>/lifecycle/update/', order_lifecycle_update_api, name='order_lifecycle_update_api'),
    path('admin-dashboard/api/purchase-analytics/', purchase_analytics_api, name='purchase_analytics_api'),
    path('admin-dashboard/api/dashboard-graphs/', dashboard_graphs_api, name='dashboard_graphs_api'),
    path('admin-dashboard/api/dashboard-kpis/', dashboard_kpis_api, name='dashboard_kpis_api'),
    path('admin-dashboard/api/dashboard-top-products/', dashboard_top_products_api, name='dashboard_top_products_api'),
    path('admin-dashboard/api/dashboard-recent-orders/', dashboard_recent_orders_api, name='dashboard_recent_orders_api'),
    path('admin-dashboard/api/announcements/', announcements_api, name='announcements_api'),
    path('admin-dashboard/api/products/bulk-import/', bulk_import_products_api, name='bulk_import_products_api'),
    path('admin-dashboard/api/editorial/', editorial_api, name='editorial_api'),
    path('admin-dashboard/api/editorial/<int:item_id>/update/', editorial_update_api, name='editorial_update_api'),
    path('admin-dashboard/api/editorial/<int:item_id>/delete/', editorial_delete_api, name='editorial_delete_api'),
    path('admin-dashboard/api/editorial/<int:item_id>/toggle/', editorial_toggle_api, name='editorial_toggle_api'),
    path('admin-dashboard/api/product-list-simple/', product_list_simple_api, name='product_list_simple_api'),

    # Collections CMS
    path('admin-dashboard/api/collections/', collections_api, name='collections_api'),
    path('admin-dashboard/api/collections/<int:collection_id>/update/', collections_update_api, name='collections_update_api'),
    path('admin-dashboard/api/collections/<int:collection_id>/delete/', collections_delete_api, name='collections_delete_api'),
    path('admin-dashboard/api/collections/<int:collection_id>/toggle/', collections_toggle_api, name='collections_toggle_api'),
    path('admin-dashboard/api/collection-rows/', collection_rows_api, name='collection_rows_api'),
    path('admin-dashboard/api/collection-rows/<int:row_id>/update/', collection_rows_update_api, name='collection_rows_update_api'),
    path('admin-dashboard/api/collection-rows/<int:row_id>/delete/', collection_rows_delete_api, name='collection_rows_delete_api'),
    path('admin-dashboard/api/zoom-carousel/', zoom_carousel_api, name='zoom_carousel_api'),
    path('admin-dashboard/api/zoom-carousel/<int:item_id>/update/', zoom_carousel_update_api, name='zoom_carousel_update_api'),
    path('admin-dashboard/api/zoom-carousel/<int:item_id>/delete/', zoom_carousel_delete_api, name='zoom_carousel_delete_api'),
    path('admin-dashboard/api/zoom-carousel/<int:item_id>/toggle/', zoom_carousel_toggle_api, name='zoom_carousel_toggle_api'),
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