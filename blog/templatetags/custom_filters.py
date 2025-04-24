from django import template

from blog.models import PostNote

register = template.Library()

@register.filter
def split(value, arg):
    """
    Splits the value by arg
    """
    return value.split(arg)


@register.filter
def strip(value):
    """
    Strips whitespace from the value
    """
    return value.strip()

@register.filter
def has_voted(comment, user):
    """Check if a user has voted on a comment"""
    return comment.votes.filter(user=user).exists()

@register.filter
def get_category_display(category):
    CATEGORY_DISPLAY_MAP = dict(PostNote.CATEGORY_CHOICES)
    return CATEGORY_DISPLAY_MAP.get(category, category)