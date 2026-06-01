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
    categories_update_api,
    categories_toggle_api,
    categories_products_api,
    product_status_trend_api,
    top_categories_revenue_api,
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
    hero_slides_api,
    hero_slide_update_api,
    hero_slide_delete_api,
    hero_slide_toggle_api,
    site_settings_api,
    coupons_api,
    coupon_update_api,
    coupon_delete_api,
    coupon_toggle_api,
    # Customer analytics & management
    customer_list_api,
    customer_orders_api,
    customer_create_api,
    customer_update_api,
    customer_toggle_api,
    customer_category_graph_api,
    top_customers_api,
    # Order management upgrade
    customer_search_api,
    create_manual_order_api,
    order_edit_items_api,
    order_update_items_api,
    orders_kanban_api,
    orders_trend_api,
    lifecycle_analytics_api,
    admin_cancel_order_api,
    admin_users_list_api,
    admin_users_create_api,
    admin_users_update_api,
    admin_users_toggle_api,
    admin_users_delete_api,
    returns_list_api,
    returns_analytics_api,
    return_detail_api,
    return_update_status_api,
    return_save_qc_api,
    return_process_refund_api,
    return_add_note_api,
    # Marketing Intelligence
    campaigns_list_api,
    campaign_create_api,
    campaign_update_api,
    campaign_delete_api,
    campaign_send_api,
    campaign_generate_ai_api,
    marketing_analytics_api,
    automation_config_api,
    automation_config_save_api,
    # Finance Intelligence
    finance_overview_api,
    finance_inventory_api,
    finance_copilot_api,
    # API Settings
    api_settings_list_api,
    api_setting_save_api,
    api_setting_delete_api,
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
    # Customer analytics & management
    path('admin-dashboard/api/customers/', customer_list_api, name='customer_list_api'),
    path('admin-dashboard/api/customers/create/', customer_create_api, name='customer_create_api'),
    path('admin-dashboard/api/customers/<int:customer_id>/orders/', customer_orders_api, name='customer_orders_api'),
    path('admin-dashboard/api/customers/<int:customer_id>/update/', customer_update_api, name='customer_update_api'),
    path('admin-dashboard/api/customers/<int:customer_id>/toggle/', customer_toggle_api, name='customer_toggle_api'),
    path('admin-dashboard/api/customer-category-graph/', customer_category_graph_api, name='customer_category_graph_api'),
    path('admin-dashboard/api/top-customers/', top_customers_api, name='top_customers_api'),
    path('admin-dashboard/api/product/<int:product_id>/', get_product_api, name='get_product_api'),
    path('admin-dashboard/api/product/<int:product_id>/edit/', edit_product_api, name='edit_product_api'),
    path('admin-dashboard/api/product/<int:product_id>/toggle-active/', toggle_product_active_api, name='toggle_product_active_api'),
    path('admin-dashboard/api/product/<int:product_id>/delete/', delete_product_api, name='delete_product_api'),
    path('admin-dashboard/api/categories/', categories_api, name='categories_api'),
    path('admin-dashboard/api/categories/<int:category_id>/delete/', delete_category_api, name='delete_category_api'),
    path('admin-dashboard/api/categories/<int:category_id>/update/', categories_update_api, name='categories_update_api'),
    path('admin-dashboard/api/categories/<int:category_id>/toggle/', categories_toggle_api, name='categories_toggle_api'),
    path('admin-dashboard/api/categories/<int:category_id>/products/', categories_products_api, name='categories_products_api'),
    path('admin-dashboard/api/product-status-trend/', product_status_trend_api, name='product_status_trend_api'),
    path('admin-dashboard/api/top-categories-revenue/', top_categories_revenue_api, name='top_categories_revenue_api'),
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

    # Hero Slides CMS
    path('admin-dashboard/api/hero-slides/', hero_slides_api, name='hero_slides_api'),
    path('admin-dashboard/api/hero-slides/<int:slide_id>/update/', hero_slide_update_api, name='hero_slide_update_api'),
    path('admin-dashboard/api/hero-slides/<int:slide_id>/delete/', hero_slide_delete_api, name='hero_slide_delete_api'),
    path('admin-dashboard/api/hero-slides/<int:slide_id>/toggle/', hero_slide_toggle_api, name='hero_slide_toggle_api'),

    # Site Settings
    path('admin-dashboard/api/site-settings/', site_settings_api, name='site_settings_api'),

    # Coupons
    path('admin-dashboard/api/coupons/', coupons_api, name='coupons_api'),
    path('admin-dashboard/api/coupons/<int:coupon_id>/update/', coupon_update_api, name='coupon_update_api'),
    path('admin-dashboard/api/coupons/<int:coupon_id>/delete/', coupon_delete_api, name='coupon_delete_api'),
    path('admin-dashboard/api/coupons/<int:coupon_id>/toggle/', coupon_toggle_api, name='coupon_toggle_api'),

    # Order management upgrade
    path('admin-dashboard/api/customer-search/', customer_search_api, name='customer_search_api'),
    path('admin-dashboard/api/manual-order/', create_manual_order_api, name='create_manual_order_api'),
    path('admin-dashboard/api/orders/<int:order_id>/edit-items/', order_edit_items_api, name='order_edit_items_api'),
    path('admin-dashboard/api/orders/<int:order_id>/update-items/', order_update_items_api, name='order_update_items_api'),
    path('admin-dashboard/api/orders-kanban/', orders_kanban_api, name='orders_kanban_api'),
    path('admin-dashboard/api/orders-trend/', orders_trend_api, name='orders_trend_api'),
    path('admin-dashboard/api/lifecycle-analytics/', lifecycle_analytics_api, name='lifecycle_analytics_api'),
    path('admin-dashboard/api/orders/<int:order_id>/cancel/', admin_cancel_order_api, name='admin_cancel_order_api'),

    # ── Marketing Intelligence ───────────────────────────────────
    path('admin-dashboard/api/campaigns/', campaigns_list_api, name='campaigns_list_api'),
    path('admin-dashboard/api/campaigns/create/', campaign_create_api, name='campaign_create_api'),
    path('admin-dashboard/api/campaigns/<int:campaign_id>/update/', campaign_update_api, name='campaign_update_api'),
    path('admin-dashboard/api/campaigns/<int:campaign_id>/delete/', campaign_delete_api, name='campaign_delete_api'),
    path('admin-dashboard/api/campaigns/<int:campaign_id>/send/', campaign_send_api, name='campaign_send_api'),
    path('admin-dashboard/api/campaigns/generate-ai/', campaign_generate_ai_api, name='campaign_generate_ai_api'),
    path('admin-dashboard/api/marketing-analytics/', marketing_analytics_api, name='marketing_analytics_api'),
    path('admin-dashboard/api/automation-config/', automation_config_api, name='automation_config_api'),
    path('admin-dashboard/api/automation-config/save/', automation_config_save_api, name='automation_config_save_api'),
    # ── Finance Intelligence ──────────────────────────────────────
    path('admin-dashboard/api/finance-overview/', finance_overview_api, name='finance_overview_api'),
    path('admin-dashboard/api/finance-inventory/', finance_inventory_api, name='finance_inventory_api'),
    path('admin-dashboard/api/finance-copilot/', finance_copilot_api, name='finance_copilot_api'),
    # ── API Settings (Misc Management) ───────────────────────────
    path('admin-dashboard/api/api-settings/', api_settings_list_api, name='api_settings_list_api'),
    path('admin-dashboard/api/api-settings/save/', api_setting_save_api, name='api_setting_save_api'),
    path('admin-dashboard/api/api-settings/<str:key>/delete/', api_setting_delete_api, name='api_setting_delete_api'),

    # Return & Refund Management
    path('admin-dashboard/api/returns/', returns_list_api, name='returns_list_api'),
    path('admin-dashboard/api/returns/analytics/', returns_analytics_api, name='returns_analytics_api'),
    path('admin-dashboard/api/returns/<int:return_id>/', return_detail_api, name='return_detail_api'),
    path('admin-dashboard/api/returns/<int:return_id>/update-status/', return_update_status_api, name='return_update_status_api'),
    path('admin-dashboard/api/returns/<int:return_id>/save-qc/', return_save_qc_api, name='return_save_qc_api'),
    path('admin-dashboard/api/returns/<int:return_id>/process-refund/', return_process_refund_api, name='return_process_refund_api'),
    path('admin-dashboard/api/returns/<int:return_id>/add-note/', return_add_note_api, name='return_add_note_api'),

    # User Management
    path('admin-dashboard/api/admin-users/', admin_users_list_api, name='admin_users_list_api'),
    path('admin-dashboard/api/admin-users/create/', admin_users_create_api, name='admin_users_create_api'),
    path('admin-dashboard/api/admin-users/<int:user_id>/update/', admin_users_update_api, name='admin_users_update_api'),
    path('admin-dashboard/api/admin-users/<int:user_id>/toggle/', admin_users_toggle_api, name='admin_users_toggle_api'),
    path('admin-dashboard/api/admin-users/<int:user_id>/delete/', admin_users_delete_api, name='admin_users_delete_api'),

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