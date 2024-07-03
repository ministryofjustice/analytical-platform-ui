from django import forms

from .models import Project


class ProjectForm(forms.ModelForm):
    resources = forms.CharField(
        widget=forms.Textarea, help_text="Comma seperated list of databases"
    )

    class Meta:
        model = Project
        fields = ["name", "review_date", "business_case"]
