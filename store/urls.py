
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

    # Checkout
    path('checkout/success/<int:order_id>/', views.order_success_view, name='order_success'),

    # Address API
    path('api/addresses/', views.addresses_api, name='addresses_api'),
    path('api/addresses/<int:addr_id>/update/', views.address_update_api, name='address_update_api'),
    path('api/addresses/<int:addr_id>/delete/', views.address_delete_api, name='address_delete_api'),
    path('api/addresses/<int:addr_id>/set-default/', views.address_set_default_api, name='address_set_default_api'),

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
]
