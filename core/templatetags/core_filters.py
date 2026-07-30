from django import template

register = template.Library()

@register.filter
def duration_display(seconds):
    try:
        seconds = int(seconds)
    except (TypeError, ValueError):
        return '—'
    m, s = divmod(seconds, 60)
    return f"{m}m {s}s" if m else f"{s}s"
