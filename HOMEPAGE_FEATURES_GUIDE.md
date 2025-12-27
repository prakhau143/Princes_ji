# Homepage Features Guide - Princess Jewelry E-commerce

## Overview
This guide explains all the new features implemented for the Princess Jewelry e-commerce website, including admin-controlled announcements and homepage product sections.

---

## 1. ANNOUNCEMENT BAR

### What is it?
A horizontal scrolling announcement bar that appears at the top of every page, just below the header. Perfect for promotions, sales, and important messages.

### How to Manage Announcements

#### Access Admin Panel:
1. Go to: `http://your-domain.com/admin/`
2. Login with admin credentials
3. Look for **"Announcements"** in the sidebar

#### Create New Announcement:
1. Click **"Add Announcement"**
2. Fill in the fields:
   - **Title** (Optional): Short heading like "SALE" or "NEW ARRIVAL"
   - **Message** (Required): Your announcement text
   - **Is Active**: Check this box to show the announcement on the website
3. Click **"Save"**

#### Features:
- ✅ Multiple announcements rotate automatically
- ✅ Smooth horizontal scrolling animation (30 seconds per cycle)
- ✅ Pauses on hover for better readability
- ✅ Beautiful gradient background (pink to purple)
- ✅ Only active announcements are displayed

#### Example Announcements:
```
Title: "FLASH SALE"
Message: "Get 30% OFF on all jewelry items! Limited time offer. Use code: PRINCESS30"

Title: "FREE SHIPPING"
Message: "Free shipping on orders above ₹2000. Shop now!"

Title: "NEW COLLECTION"
Message: "Explore our latest bridal jewelry collection. Handcrafted with love ✨"
```

---

## 2. HOMEPAGE PRODUCT SECTIONS

### What are they?
Four dedicated sections on the homepage where you can showcase specific products:

1. **Most Selling Products** - Your best-selling items
2. **Trending Products** - Currently popular items
3. **New Launch Products** - Recently added products
4. **Featured Products** - Handpicked premium items

### How to Manage Product Sections

#### Access Admin Panel:
1. Go to: `http://your-domain.com/admin/`
2. Look for **"Homepage Section Products"** in the sidebar

#### Add Products to a Section:
1. Click **"Add Homepage Section Product"**
2. Select:
   - **Section Type**: Choose from Most Selling, Trending, New Launch, or Featured
   - **Product**: Select the product from dropdown
   - **Position**: Choose position 1-4 (determines display order)
3. Click **"Save"**

#### Important Rules:
- ⚠️ **Maximum 4 products per section**
- ⚠️ Each position (1-4) must be unique within a section
- ⚠️ Only active products will be displayed on the website
- ⚠️ Products must have images for best display

#### Managing Products:
- **To Replace a Product**: Delete the old entry and add a new one
- **To Reorder Products**: Change the position numbers
- **To Remove a Product**: Simply delete the entry

#### Example Setup:
```
MOST SELLING SECTION:
- Position 1: Diamond Ring (₹15,000)
- Position 2: Gold Necklace (₹25,000)
- Position 3: Pearl Earrings (₹8,000)
- Position 4: Silver Bracelet (₹5,000)

TRENDING SECTION:
- Position 1: Rose Gold Pendant (₹12,000)
- Position 2: Emerald Ring (₹18,000)
- Position 3: Platinum Chain (₹30,000)
- Position 4: Ruby Earrings (₹20,000)
```

---

## 3. PRODUCT IMAGE MANAGEMENT

### Multiple Images per Product
Each product can now have up to **4 images total**:
- 1 Main Image (set in the Product form)
- 3 Additional Images (added via inline forms)

#### How to Add Multiple Images:
1. Go to **Products** in admin
2. Click on a product to edit
3. Scroll down to **"Product Images"** section
4. Click **"Add another Product Image"**
5. Upload up to 3 additional images
6. Click **"Save"**

#### Best Practices:
- Use high-quality images (recommended: 800x800px or higher)
- Show different angles of the product
- Include close-up details
- Use consistent lighting and background

---

## 4. PRODUCT ACTIVATION/DEACTIVATION

### What is it?
Control which products appear on the website without deleting them.

#### How to Use:
1. Go to **Products** in admin
2. Find the **"Is Active"** checkbox column
3. Check/uncheck to activate/deactivate products
4. Inactive products won't appear on the website

#### Bulk Actions:
1. Select multiple products (checkboxes)
2. Choose action from dropdown:
   - "Activate selected products"
   - "Deactivate selected products"
3. Click **"Go"**

---

## 5. VISUAL EFFECTS & ANIMATIONS

### Three.js Particle Background
- Subtle 3D particle animation in the hero section
- Mouse-reactive movement (desktop only)
- Automatically pauses when off-screen (performance optimization)
- Reduced effects on mobile devices

### GSAP Scroll Animations
- Product cards fade in as you scroll
- Smooth parallax effects on section titles
- Hover depth effects on product cards
- All animations respect user's motion preferences

### Performance Features:
- ✅ 60 FPS maintained
- ✅ IntersectionObserver pauses animations when off-screen
- ✅ Mobile-optimized (lighter effects)
- ✅ Respects "prefers-reduced-motion" setting

---

## 6. LOGIN FLOW

### Current Behavior:
- ✅ Users can browse products WITHOUT login
- ✅ Login required ONLY for:
  - Adding to cart
  - Checkout
  - Placing orders
  - Viewing order history

### User Experience:
- Non-logged-in users see product details
- "Add to Cart" buttons redirect to login
- Smooth modal-based login (no page redirect)

---

## 7. ADMIN QUICK TIPS

### Best Practices:

#### For Announcements:
- Keep messages concise (under 100 characters)
- Use emojis sparingly for visual appeal
- Update regularly to keep content fresh
- Deactivate old announcements instead of deleting

#### For Product Sections:
- Update sections weekly to keep homepage fresh
- Feature seasonal products in "New Launch"
- Put best sellers in "Most Selling"
- Use "Featured" for premium/high-margin items
- Ensure all products have good images

#### For Products:
- Always add multiple images (4 recommended)
- Write detailed descriptions
- Keep stock updated
- Use "Is Active" instead of deleting products
- Set competitive prices

---

## 8. TROUBLESHOOTING

### Announcement not showing?
- ✅ Check if "Is Active" is checked
- ✅ Verify message field is not empty
- ✅ Clear browser cache

### Product section empty?
- ✅ Ensure products are marked "Is Active"
- ✅ Check if you've added products to that section
- ✅ Verify products have images
- ✅ Check stock is greater than 0

### Images not displaying?
- ✅ Verify image file format (JPG, PNG, WebP)
- ✅ Check file size (under 5MB recommended)
- ✅ Ensure MEDIA_URL is configured correctly
- ✅ Run: `python3 manage.py collectstatic`

### Animations not working?
- ✅ Check browser console for JavaScript errors
- ✅ Ensure Three.js and GSAP CDN links are accessible
- ✅ Clear browser cache
- ✅ Try different browser

---

## 9. TECHNICAL DETAILS

### Database Models:
- `Announcement` - Stores announcement bar messages
- `ProductImage` - Stores additional product images
- `HomepageSectionProduct` - Maps products to homepage sections

### Context Processor:
- Announcements are automatically available in all templates
- No need to pass them manually in views

### Admin Customization:
- Custom validation ensures max 4 products per section
- Position uniqueness enforced
- Helpful error messages

---

## 10. SUPPORT

### Need Help?
- Check Django admin logs for errors
- Review browser console for JavaScript errors
- Ensure all migrations are applied: `python3 manage.py migrate`
- Contact technical support with screenshots

### Useful Commands:
```bash
# Create migrations
python3 manage.py makemigrations

# Apply migrations
python3 manage.py migrate

# Create admin user
python3 manage.py createsuperuser

# Collect static files
python3 manage.py collectstatic

# Run development server
python3 manage.py runserver
```

---

## 11. FUTURE ENHANCEMENTS

Potential features to add:
- [ ] Drag-and-drop product ordering
- [ ] Announcement scheduling (start/end dates)
- [ ] A/B testing for different product arrangements
- [ ] Analytics for section performance
- [ ] Bulk product import/export
- [ ] Image optimization automation

---

**Last Updated**: December 2024  
**Version**: 1.0  
**Framework**: Django 5.2.6  
**Frontend**: TailwindCSS, Three.js, GSAP
