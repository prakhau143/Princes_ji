"""
Context processors to make data available to all templates
"""
from .models import Announcement


def announcements(request):
    """
    Add active announcements to all template contexts
    """
    return {
        'announcements': Announcement.objects.filter(is_active=True)
    }
