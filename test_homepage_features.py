"""
Test script to verify all homepage features are working correctly
Run this with: python3 manage.py shell < test_homepage_features.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from store.models import Announcement, Product, Category, HomepageSectionProduct
from django.contrib.auth.models import User

print("=" * 70)
print("PRINCESS JEWELRY - HOMEPAGE FEATURES TEST")
print("=" * 70)

# Test 1: Check Announcements
print("\n1. TESTING ANNOUNCEMENTS")
print("-" * 70)
announcements = Announcement.objects.all()
active_announcements = Announcement.objects.filter(is_active=True)
print(f"✓ Total Announcements: {announcements.count()}")
print(f"✓ Active Announcements: {active_announcements.count()}")

if active_announcements.exists():
    print("\nActive Announcements:")
    for ann in active_announcements:
        print(f"  - {ann.title or 'No Title'}: {ann.message[:50]}...")
else:
    print("⚠ No active announcements found. Creating sample...")
    Announcement.objects.create(
        title="WELCOME",
        message="Welcome to Princess Jewelry! Explore our exquisite collection of handcrafted jewelry.",
        is_active=True
    )
    Announcement.objects.create(
        title="SALE",
        message="Get 20% OFF on all items! Use code: PRINCESS20 at checkout.",
        is_active=True
    )
    print("✓ Sample announcements created!")

# Test 2: Check Products
print("\n2. TESTING PRODUCTS")
print("-" * 70)
products = Product.objects.all()
active_products = Product.objects.filter(is_active=True)
print(f"✓ Total Products: {products.count()}")
print(f"✓ Active Products: {active_products.count()}")

if not active_products.exists():
    print("⚠ No active products found. Please add products via admin panel.")

# Test 3: Check Homepage Sections
print("\n3. TESTING HOMEPAGE PRODUCT SECTIONS")
print("-" * 70)

sections = ['most_selling', 'trending', 'new_launch', 'featured']
section_names = {
    'most_selling': 'Most Selling Products',
    'trending': 'Trending Products',
    'new_launch': 'New Launch Products',
    'featured': 'Featured Products'
}

for section in sections:
    section_products = HomepageSectionProduct.objects.filter(section_type=section)
    print(f"\n{section_names[section]}:")
    print(f"  Products assigned: {section_products.count()}/4")
    
    if section_products.exists():
        for sp in section_products:
            print(f"    Position {sp.position}: {sp.product.name} (₹{sp.product.price})")
    else:
        print(f"  ⚠ No products assigned to this section")
        if active_products.count() >= 4:
            print(f"  💡 Tip: Go to Admin → 🏠 Homepage Product Sections → Add products")

# Test 4: Check Context Processor
print("\n4. TESTING CONTEXT PROCESSOR")
print("-" * 70)
try:
    from store.context_processors import announcements as ann_processor
    from django.http import HttpRequest
    request = HttpRequest()
    context = ann_processor(request)
    print(f"✓ Context processor working")
    print(f"✓ Announcements in context: {context['announcements'].count()}")
except Exception as e:
    print(f"✗ Context processor error: {e}")

# Test 5: Check Admin Registration
print("\n5. TESTING ADMIN REGISTRATION")
print("-" * 70)
from django.contrib import admin
from store.models import Announcement, HomepageSectionProduct

if Announcement in admin.site._registry:
    print("✓ Announcement model registered in admin")
else:
    print("✗ Announcement model NOT registered in admin")

if HomepageSectionProduct in admin.site._registry:
    print("✓ HomepageSectionProduct model registered in admin")
else:
    print("✗ HomepageSectionProduct model NOT registered in admin")

# Summary
print("\n" + "=" * 70)
print("TEST SUMMARY")
print("=" * 70)
print(f"✓ Announcements: {active_announcements.count()} active")
print(f"✓ Products: {active_products.count()} active")

total_section_products = HomepageSectionProduct.objects.count()
print(f"✓ Homepage Sections: {total_section_products} products assigned")

if active_announcements.count() > 0 and total_section_products >= 4:
    print("\n🎉 ALL FEATURES ARE READY!")
    print("   Visit your website to see the changes.")
elif active_announcements.count() == 0:
    print("\n⚠ ACTION REQUIRED:")
    print("   1. Go to Admin Panel → 📢 Announcement Bar")
    print("   2. Add at least one announcement")
    print("   3. Make sure 'Is Active' is checked")
elif total_section_products < 4:
    print("\n⚠ ACTION REQUIRED:")
    print("   1. Go to Admin Panel → 🏠 Homepage Product Sections")
    print("   2. Add products to each section (4 products per section)")
    print("   3. Select section type, product, and position (1-4)")

print("\n" + "=" * 70)
print("ADMIN PANEL ACCESS")
print("=" * 70)
print("URL: http://127.0.0.1:8000/admin/")
print("\nLook for these sections in the sidebar:")
print("  📢 Announcement Bar")
print("  🏠 Homepage Product Sections")
print("=" * 70)
