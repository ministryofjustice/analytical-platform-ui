from django import template
from django.urls import reverse

register = template.Library()


@register.simple_tag
def database_detail_url(database):
    try:
        return database.get_absolute_url()
    except (TypeError, AttributeError):
        return reverse("database_access:detail", kwargs={"database_name": database["Name"]})


@register.simple_tag
def table_detail_url(table, database_name):
    try:
        return table.get_absolute_table_detail_url()
    except (TypeError, AttributeError):
        return reverse(
            "database_access:table_detail",
            kwargs={"database_name": database_name, "table_name": table["Name"]},
        )
