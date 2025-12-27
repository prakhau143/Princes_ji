#!/usr/bin/env python3
"""
Visual Verification Script - Shows exactly what will appear on the website
Run: python3 manage.py shell < verify_features.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from store.models import Announcement, Product, HomepageSectionProduct

def print_box(title, content, width=70):
    """Print content in a nice box"""
    print("\n" + "═" * width)
    print(f"  {title}")
    print("═" * width)
    print(content)
    print("═" * width)

# Header
print("\n" + "█" * 70)
print("█" + " " * 68 + "█")
print("█" + "  PRINCESS JEWELRY - FEATURE VERIFICATION REPORT".center(68) + "█")
print("█" + " " * 68 + "█")
print("█" * 70)

# 1. Announcement Bar Verification
announcements = Announcement.objects.filter(is_active=True)
content = ""
if announcements.exists():
    content += f"✅ STATUS: ACTIVE ({announcements.count()} announcement(s))\n\n"
    content += "What users will see on the website:\n"
    content += "─" * 70 + "\n"
    for i, ann in enumerate(announcements, 1):
        title_part = f"[{ann.title}] " if ann.title else ""
        content += f"{i}. {title_part}{ann.message}\n"
    content += "─" * 70 + "\n"
    content += "\n📍 Location: Top of every page (below header)\n"
    content += "🎬 Animation: Horizontal scroll, 30s cycle, pauses on hover\n"
    content += "🎨 Style: Pink-purple gradient background\n"
else:
    content += "❌ STATUS: NO ACTIVE ANNOUNCEMENTS\n\n"
    content += "Action Required:\n"
    content += "1. Go to: http://127.0.0.1:8000/admin/\n"
    content += "2. Click: 📢 Announcement Bar\n"
    content += "3. Add at least one announcement\n"
    content += "4. Check 'Is Active' box\n"

print_box("1️⃣  ANNOUNCEMENT BAR", content)

# 2. Homepage Sections Verification
sections = {
    'most_selling': ('🔥 MOST SELLING PRODUCTS', 'Red "Best Seller" badge'),
    'trending': ('📈 TRENDING PRODUCTS', 'Pink "Trending" badge'),
    'new_launch': ('✨ NEW LAUNCH PRODUCTS', 'Purple "New" badge'),
    'featured': ('⭐ FEATURED PRODUCTS', 'Yellow "Featured" badge')
}

for section_key, (section_title, badge_info) in sections.items():
    section_products = HomepageSectionProduct.objects.filter(
        section_type=section_key
    ).select_related('product').order_by('position')
    
    content = ""
    if section_products.exists():
        content += f"✅ STATUS: ACTIVE ({section_products.count()}/4 products)\n\n"
        content += "What users will see on the website:\n"
        content += "─" * 70 + "\n"
        for sp in section_products:
            stock_status = "✓ In Stock" if sp.product.stock > 0 else "✗ Out of Stock"
            content += f"Position {sp.position}: {sp.product.name}\n"
            content += f"             Price: ₹{sp.product.price} | {stock_status}\n"
            if sp.product.image:
                content += f"             Image: ✓ Available\n"
            else:
                content += f"             Image: ⚠ No image (will show placeholder)\n"
            content += "\n"
        content += "─" * 70 + "\n"
        content += f"\n🎨 Badge: {badge_info}\n"
        content += "📍 Location: Homepage, after hero section\n"
        content += "🎬 Animation: Fade in on scroll, hover zoom effect\n"
    else:
        content += "❌ STATUS: NO PRODUCTS ASSIGNED\n\n"
        content += "Action Required:\n"
        content += "1. Go to: http://127.0.0.1:8000/admin/\n"
        content += "2. Click: 🏠 Homepage Product Sections\n"
        content += "3. Click: Add Homepage Section Product\n"
        content += f"4. Select Section: {section_title}\n"
        content += "5. Choose Product and Position (1-4)\n"
        content += "6. Save\n"
        content += "7. Repeat for 4 products total\n"
    
    section_number = list(sections.keys()).index(section_key) + 2
    print_box(f"{section_number}️⃣  {section_title}", content)

# Summary
print("\n" + "█" * 70)
print("█" + " " * 68 + "█")
print("█" + "  SUMMARY & NEXT STEPS".center(68) + "█")
print("█" + " " * 68 + "█")
print("█" * 70)

total_announcements = Announcement.objects.filter(is_active=True).count()
total_section_products = HomepageSectionProduct.objects.count()
total_products = Product.objects.filter(is_active=True).count()

print(f"\n📊 Database Status:")
print(f"   • Active Announcements: {total_announcements}")
print(f"   • Active Products: {total_products}")
print(f"   • Homepage Section Products: {total_section_products}/16 (4 per section)")

if total_announcements > 0 and total_section_products >= 16:
    print("\n🎉 ALL FEATURES ARE FULLY CONFIGURED!")
    print("\n✅ Your website is ready with:")
    print("   • Announcement bar with scrolling messages")
    print("   • 4 homepage product sections (Most Selling, Trending, New Launch, Featured)")
    print("   • Three.js particle animations")
    print("   • GSAP scroll animations")
    print("   • Premium hover effects")
    print("\n🌐 View your website:")
    print("   http://127.0.0.1:8000/")
    print("\n⚙️  Manage content:")
    print("   http://127.0.0.1:8000/admin/")
    print("   → 📢 Announcement Bar")
    print("   → 🏠 Homepage Product Sections")
else:
    print("\n⚠️  ACTION REQUIRED:")
    if total_announcements == 0:
        print("   • Add announcements via Admin → 📢 Announcement Bar")
    if total_section_products < 16:
        missing = 16 - total_section_products
        print(f"   • Add {missing} more products to homepage sections")
        print("   • Go to Admin → 🏠 Homepage Product Sections")
    
    print("\n💡 Quick Fix:")
    print("   Run this command to auto-populate sections:")
    print("   python3 manage.py shell < populate_homepage_sections.py")

print("\n" + "█" * 70)
print()

# Admin URLs
print("🔗 QUICK LINKS:")
print("─" * 70)
print("Homepage:        http://127.0.0.1:8000/")
print("Admin Panel:     http://127.0.0.1:8000/admin/")
print("Announcements:   http://127.0.0.1:8000/admin/store/announcement/")
print("Homepage Sections: http://127.0.0.1:8000/admin/store/homepagesectionproduct/")
print("Products:        http://127.0.0.1:8000/admin/store/product/")
print("─" * 70)
print()
