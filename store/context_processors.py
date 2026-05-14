"""
Context processors to make data available to all templates
"""
from .models import Announcement, Collection, SiteSettings


def announcements(request):
    """
    Add active announcements to all template contexts
    """
    return {
        'announcements': Announcement.objects.filter(is_active=True)
    }


def active_collections(request):
	return {
		'active_collections': Collection.objects.filter(is_active=True).exclude(slug__contains='/').order_by('order', 'title')
	}


def site_settings(request):
	s = SiteSettings.get_settings()
	return {
		'glass_flash_enabled': s.glass_flash_enabled,
		'razorpay_key_id': s.razorpay_key_id,
		'cod_fee': float(s.cod_fee),
	}
