"""
Custom Admin Site Grouping for Homepage Management
This creates a cleaner admin interface with grouped sections
"""
from django.contrib import admin
from django.contrib.admin import AdminSite


class HomepageAdminSite(AdminSite):
    """Custom admin site for homepage management"""
    site_header = 'Princess Jewelry - Homepage Management'
    site_title = 'Homepage Admin'
    index_title = 'Manage Homepage Content'


# Create custom admin site instance
homepage_admin_site = HomepageAdminSite(name='homepage_admin')
