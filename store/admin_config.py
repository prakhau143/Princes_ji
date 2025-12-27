"""
Custom Admin Site Configuration for Homepage Product Sections
This creates a grouped menu structure in Django Admin
"""
from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect


class HomepageProductSectionsAdminSite(admin.AdminSite):
    site_header = "Princess Jewelry - Homepage Sections"
    site_title = "Homepage Product Sections"
    index_title = "Manage Homepage Product Sections"


# Create a custom admin site instance
homepage_sections_admin = HomepageProductSectionsAdminSite(name='homepage_sections')
