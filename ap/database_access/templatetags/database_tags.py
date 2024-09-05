from django import template
from django.urls import reverse

register = template.Library()


@register.simple_tag
def database_name(database):
    try:
        return database.name
    except AttributeError:
        return database["Name"]


@register.simple_tag
def database_url(database):
    try:
        return database.get_absolute_url()
    except (TypeError, AttributeError):
        return reverse("database_access:detail", kwargs={"database_name": database["Name"]})
