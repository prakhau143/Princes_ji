"""
Context processors to make data available to all templates
"""
from .models import Announcement, Collection


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
