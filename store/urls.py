
from django.urls import path
from . import views

urlpatterns = [
    # Note: Authentication URLs are handled in main ecommerce/urls.py
    # User profile
    path('profile/', views.profile_view, name='profile'),
    path('orders/', views.order_history_view, name='order_history'),
    path('orders/<int:order_id>/', views.order_detail_view, name='order_detail'),
    path('orders/<int:order_id>/items/<int:item_id>/review/', views.add_order_item_review_view, name='add_order_item_review'),
    # Product catalog
    path('products/', views.product_list_view, name='product_list'),
    path('products/<int:pk>/', views.product_detail_view, name='product_detail'),
    path('category/<int:category_id>/', views.category_products_view, name='category_products'),

    # Cart (page + legacy)
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart_view, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart_view, name='remove_from_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_item_quantity, name='update_cart_item_quantity'),

    # Cart JSON APIs (slide-in panel)
    path('api/cart/', views.cart_data_api, name='cart_data_api'),
    path('api/cart/update/', views.cart_update_api, name='cart_update_api'),
    path('api/cart/remove/', views.cart_remove_api, name='cart_remove_api'),
    path('api/cart/apply-coupon/', views.apply_coupon_api, name='apply_coupon_api'),
    path('api/cart/recommended/', views.recommended_products_api, name='recommended_products_api'),

    # Order confirmation (new) + legacy success redirect
    path('order-confirmation/<int:order_id>/', views.order_confirmation_view, name='order_confirmation'),
    path('checkout/success/<int:order_id>/', views.order_confirmation_view, name='order_success'),

    # Address API
    path('api/addresses/', views.addresses_api, name='addresses_api'),
    path('api/addresses/<int:addr_id>/update/', views.address_update_api, name='address_update_api'),
    path('api/addresses/<int:addr_id>/delete/', views.address_delete_api, name='address_delete_api'),
    path('api/addresses/<int:addr_id>/set-default/', views.address_set_default_api, name='address_set_default_api'),

    # Order actions
    path('api/orders/<int:order_id>/timeline/', views.order_timeline_api, name='order_timeline_api'),
    path('api/orders/<int:order_id>/cancel/', views.cancel_order_api, name='cancel_order_api'),
    path('api/orders/<int:order_id>/buy-again/', views.buy_again_api, name='buy_again_api'),

    # Order placement + Razorpay
    path('api/place-order/', views.place_order_api, name='place_order_api'),
    path('api/create-razorpay-order/', views.create_razorpay_order_api, name='create_razorpay_order_api'),
    path('api/verify-payment/', views.verify_payment_api, name='verify_payment_api'),

    # Footer pages
    path('contact/', views.contact_view, name='contact'),
    path('size-guide/', views.size_guide_view, name='size_guide'),
    path('care-instructions/', views.care_instructions_view, name='care_instructions'),
    path('shipping-returns/', views.shipping_returns_view, name='shipping_returns'),
    path('newsletter-subscribe/', views.newsletter_subscribe_view, name='newsletter_subscribe'),

    # Wishlist
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/toggle/<int:product_id>/', views.toggle_wishlist_view, name='toggle_wishlist'),

    # Collections
    path('collections/', views.collections_list_view, name='collections_list'),
    path('collections/<slug:slug>/', views.collection_detail_view, name='collection_detail'),

    # Mobile menu API
    path('api/categories-with-previews/', views.categories_with_previews_api, name='categories_with_previews'),

    # Return & Refund (user-side)
    path('returns/', views.returns_page_view, name='returns_page'),
    path('api/returns/lookup-order/', views.returns_lookup_order_api, name='returns_lookup_order_api'),
    path('api/returns/submit/', views.returns_submit_api, name='returns_submit_api'),
    path('api/returns/my-requests/', views.returns_my_requests_api, name='returns_my_requests_api'),

    # User notifications
    path('api/notifications/', views.user_notifications_api, name='user_notifications_api'),
    path('api/notifications/<int:notif_id>/read/', views.user_mark_notification_read_api, name='user_mark_notification_read_api'),
    path('api/notifications/mark-all-read/', views.user_mark_all_notifications_read_api, name='user_mark_all_notifications_read_api'),
]
