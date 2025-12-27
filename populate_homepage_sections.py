"""
Populate Homepage Sections with Sample Products
Run this with: python3 manage.py shell < populate_homepage_sections.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from store.models import Product, HomepageSectionProduct

print("=" * 70)
print("POPULATING HOMEPAGE SECTIONS WITH SAMPLE PRODUCTS")
print("=" * 70)

# Get active products
products = list(Product.objects.filter(is_active=True, stock__gt=0))

if len(products) < 4:
    print("✗ Not enough active products with stock. Need at least 4 products.")
    print(f"  Currently have: {len(products)} products")
    print("  Please add more products via admin panel.")
    exit()

print(f"\n✓ Found {len(products)} active products with stock")

# Clear existing homepage sections
HomepageSectionProduct.objects.all().delete()
print("✓ Cleared existing homepage sections")

# Define sections
sections = {
    'most_selling': 'Most Selling Products',
    'trending': 'Trending Products',
    'new_launch': 'New Launch Products',
    'featured': 'Featured Products'
}

# Populate each section with 4 products
product_index = 0
for section_key, section_name in sections.items():
    print(f"\n{section_name}:")
    for position in range(1, 5):
        if product_index < len(products):
            product = products[product_index]
            HomepageSectionProduct.objects.create(
                section_type=section_key,
                product=product,
                position=position
            )
            print(f"  Position {position}: {product.name} (₹{product.price})")
            product_index += 1
        else:
            # Reuse products if we don't have enough
            product_index = 0
            product = products[product_index]
            HomepageSectionProduct.objects.create(
                section_type=section_key,
                product=product,
                position=position
            )
            print(f"  Position {position}: {product.name} (₹{product.price})")
            product_index += 1

print("\n" + "=" * 70)
print("✓ HOMEPAGE SECTIONS POPULATED SUCCESSFULLY!")
print("=" * 70)
print("\nTotal products assigned:", HomepageSectionProduct.objects.count())
print("\nVisit your homepage to see the changes:")
print("  http://127.0.0.1:8000/")
print("\nTo manage sections, go to admin:")
print("  http://127.0.0.1:8000/admin/")
print("  → 🏠 Homepage Product Sections")
print("=" * 70)
